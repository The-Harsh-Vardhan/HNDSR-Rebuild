#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import readline from "node:readline/promises";
import process from "node:process";

import { chromium } from "playwright";

function parseArgs(argv) {
  const parsed = {
    mode: "run-editor",
    headless: false,
    dryRun: false,
    timeoutMs: 120000,
    channel: undefined,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    const next = argv[index + 1];
    if (token === "--mode") {
      parsed.mode = next;
      index += 1;
    } else if (token === "--kernel-id") {
      parsed.kernelId = next;
      index += 1;
    } else if (token === "--secret-name") {
      parsed.secretName = next;
      index += 1;
    } else if (token === "--profile-dir") {
      parsed.profileDir = next;
      index += 1;
    } else if (token === "--debug-dir") {
      parsed.debugDir = next;
      index += 1;
    } else if (token === "--timeout-ms") {
      parsed.timeoutMs = Number.parseInt(next, 10);
      index += 1;
    } else if (token === "--channel") {
      parsed.channel = next;
      index += 1;
    } else if (token === "--headless") {
      parsed.headless = true;
    } else if (token === "--headed") {
      parsed.headless = false;
    } else if (token === "--dry-run") {
      parsed.dryRun = true;
    } else {
      throw new Error(`Unknown argument: ${token}`);
    }
  }
  for (const required of ["kernelId", "secretName", "profileDir", "debugDir"]) {
    if (!parsed[required]) {
      throw new Error(`Missing required argument: ${required}`);
    }
  }
  return parsed;
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function writeDebugArtifacts(page, debugDir, stem) {
  await ensureDir(debugDir);
  await page.screenshot({ path: path.join(debugDir, `${stem}.png`), fullPage: true }).catch(() => {});
  const html = await page.content().catch(() => "");
  if (html) {
    await fs.writeFile(path.join(debugDir, `${stem}.html`), html, "utf8");
  }
}

async function firstVisible(locators, timeoutMs) {
  for (const locator of locators) {
    try {
      await locator.first().waitFor({ state: "visible", timeout: timeoutMs });
      return locator.first();
    } catch {
      // Try the next locator.
    }
  }
  return null;
}

async function promptForLogin() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  await rl.question("Log in to Kaggle in the opened browser profile, then press Enter to continue.");
  rl.close();
}

function kernelUrls(kernelId) {
  const notebookUrl = `https://www.kaggle.com/code/${kernelId}`;
  return {
    notebookUrl,
    editorUrl: `${notebookUrl}/edit`,
  };
}

async function ensureLoggedIn(page, debugDir) {
  const marker = await firstVisible(
    [
      page.getByRole("link", { name: /sign in/i }),
      page.getByRole("button", { name: /sign in/i }),
      page.getByText(/create an account/i),
    ],
    3000,
  );
  if (!marker) {
    return;
  }
  await writeDebugArtifacts(page, debugDir, "login-required");
  console.log("Kaggle login was not available in the persistent browser profile.");
  await promptForLogin();
}

async function openEditor(page, urls, debugDir) {
  await page.goto(urls.editorUrl, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle").catch(() => {});
  await ensureLoggedIn(page, debugDir);
  await page.goto(urls.editorUrl, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle").catch(() => {});

  let addOnsButton = await firstVisible(
    [
      page.getByRole("button", { name: /add-?ons/i }),
      page.getByText(/add-?ons/i),
      page.locator("button").filter({ hasText: /add-?ons/i }),
    ],
    10000,
  );
  if (addOnsButton) {
    return addOnsButton;
  }

  const editButton = await firstVisible(
    [
      page.getByRole("button", { name: /edit/i }),
      page.getByRole("button", { name: /resume/i }),
      page.getByRole("link", { name: /edit/i }),
    ],
    5000,
  );
  if (editButton) {
    await editButton.click();
    await page.waitForLoadState("networkidle").catch(() => {});
    addOnsButton = await firstVisible(
      [
        page.getByRole("button", { name: /add-?ons/i }),
        page.getByText(/add-?ons/i),
      ],
      10000,
    );
    if (addOnsButton) {
      return addOnsButton;
    }
  }

  await writeDebugArtifacts(page, debugDir, "editor-not-found");
  throw new Error("Could not reach the Kaggle notebook editor. Check the notebook slug and login state.");
}

async function openSecretsPanel(page, addOnsButton, debugDir) {
  await addOnsButton.click();
  const secretsButton = await firstVisible(
    [
      page.getByRole("menuitem", { name: /secrets/i }),
      page.getByRole("button", { name: /secrets/i }),
      page.getByText(/^Secrets$/),
    ],
    10000,
  );
  if (!secretsButton) {
    await writeDebugArtifacts(page, debugDir, "secrets-menu-missing");
    throw new Error("Kaggle editor Add-ons menu did not expose a Secrets entry.");
  }
  await secretsButton.click();
  await page.waitForLoadState("networkidle").catch(() => {});
}

async function ensureSecretAttached(page, secretName, debugDir) {
  const secretLabel = await firstVisible(
    [
      page.getByText(new RegExp(`^${secretName}$`, "i")),
      page.getByRole("row").filter({ hasText: new RegExp(secretName, "i") }),
      page.locator("label").filter({ hasText: new RegExp(secretName, "i") }),
      page.locator("div").filter({ hasText: new RegExp(secretName, "i") }),
    ],
    10000,
  );
  if (!secretLabel) {
    await writeDebugArtifacts(page, debugDir, "secret-not-listed");
    throw new Error(`The Kaggle editor did not list the ${secretName} account secret.`);
  }

  const checkbox = page.getByRole("checkbox", { name: new RegExp(secretName, "i") });
  if ((await checkbox.count()) > 0) {
    const control = checkbox.first();
    if (!(await control.isChecked())) {
      await control.check();
    }
    return;
  }

  const switchControl = page.getByRole("switch", { name: new RegExp(secretName, "i") });
  if ((await switchControl.count()) > 0) {
    const control = switchControl.first();
    const state = await control.getAttribute("aria-checked");
    if (state !== "true") {
      await control.click();
    }
    return;
  }

  const container = secretLabel.locator("xpath=ancestor::*[self::li or self::tr or self::div][1]");
  const attachButton = await firstVisible(
    [
      container.getByRole("button", { name: /attach|add|enable|select/i }),
      page.getByRole("button", { name: new RegExp(`${secretName}.*(attach|add|enable|select)`, "i") }),
    ],
    3000,
  );
  if (!attachButton) {
    await writeDebugArtifacts(page, debugDir, "secret-control-missing");
    throw new Error(`The Kaggle editor listed ${secretName} but no attach control was visible.`);
  }
  await attachButton.click();
}

async function closeSecretsPanel(page) {
  const closeButton = await firstVisible(
    [
      page.getByRole("button", { name: /done/i }),
      page.getByRole("button", { name: /^save$/i }),
      page.getByRole("button", { name: /close/i }),
      page.getByRole("button", { name: /apply/i }),
    ],
    5000,
  );
  if (closeButton) {
    await closeButton.click().catch(() => {});
    await page.waitForLoadState("networkidle").catch(() => {});
  } else {
    await page.keyboard.press("Escape").catch(() => {});
  }
}

async function launchRun(page, debugDir) {
  const saveVersionButton = await firstVisible(
    [
      page.getByRole("button", { name: /save version/i }),
      page.getByRole("button", { name: /save & run all/i }),
      page.getByRole("button", { name: /run all/i }),
    ],
    10000,
  );
  if (!saveVersionButton) {
    await writeDebugArtifacts(page, debugDir, "save-version-missing");
    throw new Error("Could not find Kaggle's Save Version or Run All action.");
  }
  await saveVersionButton.click();

  const confirmButton = await firstVisible(
    [
      page.getByRole("button", { name: /save & run all/i }),
      page.getByRole("button", { name: /run all/i }),
      page.getByRole("button", { name: /^save$/i }),
      page.getByRole("button", { name: /save version/i }),
    ],
    10000,
  );
  if (confirmButton) {
    await confirmButton.click();
  }

  const runningMarker = await firstVisible(
    [
      page.getByText(/queued/i),
      page.getByText(/running/i),
      page.getByText(/saved version/i),
      page.getByText(/version saved/i),
    ],
    15000,
  );
  if (!runningMarker) {
    await writeDebugArtifacts(page, debugDir, "run-launch-unconfirmed");
    throw new Error("The editor did not confirm that the notebook version was queued or running.");
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const urls = kernelUrls(args.kernelId);
  if (args.dryRun) {
    console.log(
      JSON.stringify(
        {
          mode: args.mode,
          kernelId: args.kernelId,
          notebookUrl: urls.notebookUrl,
          editorUrl: urls.editorUrl,
          secretName: args.secretName,
          profileDir: args.profileDir,
          debugDir: args.debugDir,
          channel: args.channel,
          headless: args.headless,
          timeoutMs: args.timeoutMs,
        },
        null,
        2,
      ),
    );
    return;
  }

  const context = await chromium.launchPersistentContext(args.profileDir, {
    channel: args.channel,
    headless: args.headless,
    viewport: { width: 1440, height: 1024 },
  });
  const page = context.pages()[0] ?? (await context.newPage());
  page.setDefaultTimeout(args.timeoutMs);

  try {
    const addOnsButton = await openEditor(page, urls, args.debugDir);
    await openSecretsPanel(page, addOnsButton, args.debugDir);
    await ensureSecretAttached(page, args.secretName, args.debugDir);
    await closeSecretsPanel(page);
    await writeDebugArtifacts(page, args.debugDir, "secret-ready");
    if (args.mode === "run-editor") {
      await launchRun(page, args.debugDir);
      await writeDebugArtifacts(page, args.debugDir, "run-launched");
    }
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exit(1);
});
