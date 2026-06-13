#!/usr/bin/env node

const fs = require("fs-extra");
const path = require("path");

const command = process.argv[2];
const arg = process.argv[3];

if (command === "init") {
  if (!arg) {
    console.log("❌ Please provide a project name");
    process.exit(1);
  }

  const projectPath = path.join(process.cwd(), arg);

  fs.ensureDirSync(projectPath);

  fs.writeFileSync(path.join(projectPath, "PROJECT_STATE.md"), "# Project State\n\n");
  fs.writeFileSync(path.join(projectPath, "TODO.md"), "# TODO\n\n");
  fs.writeFileSync(path.join(projectPath, "DECISIONS.md"), "# Decisions\n\n");
  fs.writeFileSync(path.join(projectPath, "RISK_POLICY.md"), "# Risk Policy\n\n");
  fs.writeFileSync(path.join(projectPath, "PRODUCT_VISION.md"), "# Product Vision\n\n");

  console.log(`✅ KISS project "${arg}" initialized`);
} 

else if (command === "status") {
  const filePath = path.join(process.cwd(), "PROJECT_STATE.md");

  if (!fs.existsSync(filePath)) {
    console.log("❌ No PROJECT_STATE.md found. Run 'kiss init' first.");
    process.exit(1);
  }

  const content = fs.readFileSync(filePath, "utf-8");

  console.log("📊 Project Status:\n");
  console.log(content);
} 

else if (command === "request") {
  const request = process.argv.slice(3).join(" ");

  if (!request) {
    console.log("❌ Please provide a feature request");
    process.exit(1);
  }

  const decisionsPath = path.join(process.cwd(), "DECISIONS.md");
  const todoPath = path.join(process.cwd(), "TODO.md");

  // ✅ ensure inside a project
  if (!fs.existsSync(decisionsPath)) {
    console.log("❌ Not a KISS project. Run 'kiss init' first.");
    process.exit(1);
  }

  // ✅ logic
  const risky = /login|auth|account|backend|server|sync|cloud/i.test(request);
  const premature = /add|new|feature|ai|scanner/i.test(request);

  if (risky) {
    const entry = `\n## 🚫 Blocked Request\n- ${request}\n- Reason: violates risk policy\n`;
    fs.appendFileSync(decisionsPath, entry);

    console.log("🚫 Blocked: violates risk policy");
  } 

  else if (premature) {
    const entry = `\n## ⚠️ Not Recommended\n- ${request}\n- Reason: premature (stabilize current system first)\n`;
    fs.appendFileSync(decisionsPath, entry);

    console.log("⚠️ Not recommended: stabilize current system first");
  } 

  else {
    fs.appendFileSync(todoPath, `\n- ${request}\n`);

    const entry = `\n## ✅ Accepted Request\n- ${request}\n- Reason: valid and in scope\n`;
    fs.appendFileSync(decisionsPath, entry);

    console.log("✅ Accepted");
    console.log("📝 Added to TODO.md");
  }
}

else {
  console.log("❌ Unknown command");
}
