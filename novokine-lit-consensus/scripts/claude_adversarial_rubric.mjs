#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const here = path.dirname(new URL(import.meta.url).pathname);
const skillRoot = path.resolve(here, "..");
const rubricPath = path.join(skillRoot, "references", "adversarial_rubric.json");
const rubricMdPath = path.join(skillRoot, "references", "adversarial_rubric.md");

const requiredAgentFields = [
  "id",
  "name",
  "adversarial_question",
  "failure_modes",
  "required_checks",
  "red_flags",
  "pass_standard",
  "output_fields"
];

const requiredDesignAgentFields = [
  "id",
  "name",
  "design_principle",
  "required_fields",
  "decision_rules",
  "failure_tests",
  "acceptance_standard",
  "rubric_contribution"
];

const jsonSchema = {
  type: "object",
  required: [
    "schema_version",
    "rubric_owner",
    "purpose",
    "design_process",
    "rubric_design_agents",
    "do_not_use",
    "decision_lanes",
    "adversarial_agents",
    "final_decision_protocol",
    "target_output_requirements",
    "pair_output_requirements"
  ],
  properties: {
    schema_version: { type: "string" },
    rubric_owner: { type: "string" },
    purpose: { type: "string" },
    modality: { type: "string" },
    design_process: { type: "object" },
    rubric_design_agents: { type: "array", items: { type: "object" } },
    do_not_use: { type: "array", items: { type: "string" } },
    decision_lanes: { type: "array", items: { type: "object" } },
    evidence_hierarchy: { type: "array", items: { type: "string" } },
    intervention_translation: { type: "array", items: { type: "object" } },
    adversarial_agents: { type: "array", items: { type: "object" } },
    final_decision_protocol: { type: "array", items: { type: "string" } },
    target_output_requirements: { type: "array", items: { type: "string" } },
    pair_output_requirements: { type: "array", items: { type: "string" } }
  }
};

function usage() {
  console.log(`Usage:
  node scripts/claude_adversarial_rubric.mjs --dry-run [--input path/to/rubric.json]
  node scripts/claude_adversarial_rubric.mjs --render-md [--input path/to/rubric.json]
  node scripts/claude_adversarial_rubric.mjs --write

--dry-run validates the checked-in adversarial rubric without calling Claude.
--render-md validates JSON and rewrites references/adversarial_rubric.md.
--write asks Claude Agent SDK to regenerate the JSON rubric, validates it, and rewrites JSON + Markdown.`);
}

function parseArgs(argv) {
  const out = { mode: "dry-run", input: rubricPath };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") out.help = true;
    else if (arg === "--dry-run") out.mode = "dry-run";
    else if (arg === "--render-md") out.mode = "render-md";
    else if (arg === "--write") out.mode = "write";
    else if (arg === "--input") {
      i += 1;
      if (!argv[i]) throw new Error("--input requires a path");
      out.input = path.resolve(argv[i]);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return out;
}

function mustArray(value, name) {
  if (!Array.isArray(value)) throw new Error(`${name} must be an array`);
  return value;
}

function validateRubric(rubric) {
  if (rubric.schema_version !== "novokine-adversarial-rubric-v1") {
    throw new Error(`schema_version must be novokine-adversarial-rubric-v1, got ${rubric.schema_version}`);
  }
  if (rubric.rubric_owner !== "claude-agent-sdk") {
    throw new Error(`rubric_owner must be claude-agent-sdk, got ${rubric.rubric_owner}`);
  }
  if (!rubric.design_process || typeof rubric.design_process !== "object") {
    throw new Error("design_process must be an object");
  }
  if (rubric.design_process.agent_count !== 10) {
    throw new Error(`design_process.agent_count must be 10, got ${rubric.design_process.agent_count}`);
  }
  if (!String(rubric.design_process.method || "").toLowerCase().includes("design")) {
    throw new Error("design_process.method must describe the adversarial design process");
  }
  const designAgents = mustArray(rubric.rubric_design_agents, "rubric_design_agents");
  if (designAgents.length !== 10) {
    throw new Error(`rubric_design_agents must contain exactly 10 design agents, got ${designAgents.length}`);
  }
  const designIds = new Set();
  for (const [idx, agent] of designAgents.entries()) {
    for (const field of requiredDesignAgentFields) {
      if (!(field in agent)) throw new Error(`rubric_design_agents[${idx}] missing ${field}`);
    }
    if (designIds.has(agent.id)) throw new Error(`duplicate rubric design agent id: ${agent.id}`);
    designIds.add(agent.id);
    for (const field of ["required_fields", "decision_rules", "failure_tests"]) {
      if (!Array.isArray(agent[field]) || agent[field].length < 3) {
        throw new Error(`design agent ${agent.id}.${field} must have at least 3 entries`);
      }
    }
  }
  const agents = mustArray(rubric.adversarial_agents, "adversarial_agents");
  if (agents.length !== 10) {
    throw new Error(`adversarial_agents must contain exactly 10 agents, got ${agents.length}`);
  }
  const ids = new Set();
  for (const [idx, agent] of agents.entries()) {
    for (const field of requiredAgentFields) {
      if (!(field in agent)) throw new Error(`adversarial_agents[${idx}] missing ${field}`);
    }
    if (ids.has(agent.id)) throw new Error(`duplicate adversarial agent id: ${agent.id}`);
    ids.add(agent.id);
    for (const field of ["failure_modes", "required_checks", "red_flags", "output_fields"]) {
      if (!Array.isArray(agent[field]) || agent[field].length < 3) {
        throw new Error(`agent ${agent.id}.${field} must have at least 3 entries`);
      }
    }
  }
  const laneIds = new Set(mustArray(rubric.decision_lanes, "decision_lanes").map((lane) => lane.id));
  for (const required of ["activation_direction", "novokine_likelihood", "evidence_provenance"]) {
    if (!laneIds.has(required)) throw new Error(`decision_lanes missing ${required}`);
  }
  const doNotUse = mustArray(rubric.do_not_use, "do_not_use");
  for (const forbidden of ["differential expression as activation direction", "Open Targets as activation direction"]) {
    if (!doNotUse.includes(forbidden)) throw new Error(`do_not_use missing ${forbidden}`);
  }
  if (!mustArray(rubric.target_output_requirements, "target_output_requirements").includes("adversarial_review")) {
    throw new Error("target_output_requirements must include adversarial_review");
  }
  if (!mustArray(rubric.pair_output_requirements, "pair_output_requirements").includes("adversarial_review")) {
    throw new Error("pair_output_requirements must include adversarial_review");
  }
}

function renderMarkdown(rubric) {
  const lines = [];
  lines.push("# Adversarial Novokine Literature Rubric");
  lines.push("");
  lines.push(`Schema: \`${rubric.schema_version}\``);
  lines.push("");
  lines.push(rubric.purpose);
  lines.push("");
  if (rubric.design_process) {
    lines.push("## Rubric Design Process");
    lines.push("");
    lines.push(`Method: ${rubric.design_process.method}`);
    lines.push("");
    lines.push(`Design agents: ${rubric.design_process.agent_count}`);
    lines.push("");
    if (rubric.design_process.design_goal) {
      lines.push(`Design goal: ${rubric.design_process.design_goal}`);
      lines.push("");
    }
    if (rubric.design_process.synthesis_rule) {
      lines.push(`Synthesis rule: ${rubric.design_process.synthesis_rule}`);
      lines.push("");
    }
  }
  if (rubric.rubric_design_agents) {
    lines.push("## 10 Adversarial Design Agents");
    lines.push("");
    for (const [idx, agent] of rubric.rubric_design_agents.entries()) {
      lines.push(`### ${idx + 1}. ${agent.name} (${agent.id})`);
      lines.push("");
      lines.push(agent.design_principle);
      lines.push("");
      lines.push("Required fields:");
      for (const item of agent.required_fields) lines.push(`- ${item}`);
      lines.push("");
      lines.push("Decision rules:");
      for (const item of agent.decision_rules) lines.push(`- ${item}`);
      lines.push("");
      lines.push("Failure tests:");
      for (const item of agent.failure_tests) lines.push(`- ${item}`);
      lines.push("");
      lines.push(`Acceptance standard: ${agent.acceptance_standard}`);
      lines.push("");
      lines.push(`Rubric contribution: ${agent.rubric_contribution}`);
      lines.push("");
    }
  }
  lines.push("## Non-Negotiables");
  lines.push("");
  for (const item of rubric.do_not_use) lines.push(`- ${item}`);
  lines.push("");
  lines.push("## Decision Lanes");
  lines.push("");
  for (const lane of rubric.decision_lanes) {
    lines.push(`### ${lane.id}`);
    lines.push("");
    lines.push(lane.question);
    if (lane.allowed_values) lines.push(`Allowed values: ${lane.allowed_values.map((v) => `\`${v}\``).join(", ")}`);
    if (lane.minimum_evidence) lines.push(`Minimum evidence: ${lane.minimum_evidence}`);
    lines.push("");
  }
  lines.push("## 10 Adversarial Agents");
  lines.push("");
  for (const [idx, agent] of rubric.adversarial_agents.entries()) {
    lines.push(`### ${idx + 1}. ${agent.name} (${agent.id})`);
    lines.push("");
    lines.push(`Question: ${agent.adversarial_question}`);
    lines.push("");
    lines.push("Failure modes:");
    for (const item of agent.failure_modes) lines.push(`- ${item}`);
    lines.push("");
    lines.push("Required checks:");
    for (const item of agent.required_checks) lines.push(`- ${item}`);
    lines.push("");
    lines.push("Red flags:");
    for (const item of agent.red_flags) lines.push(`- ${item}`);
    lines.push("");
    lines.push(`Pass standard: ${agent.pass_standard}`);
    lines.push("");
    lines.push(`Output fields: ${agent.output_fields.map((field) => `\`${field}\``).join(", ")}`);
    lines.push("");
  }
  lines.push("## Final Decision Protocol");
  lines.push("");
  for (const item of rubric.final_decision_protocol) lines.push(`- ${item}`);
  lines.push("");
  return `${lines.join("\n")}\n`;
}

async function readRubric(inputPath) {
  return JSON.parse(await fs.readFile(inputPath, "utf8"));
}

async function generateWithClaude(current) {
  let query;
  try {
    ({ query } = await import("@anthropic-ai/claude-agent-sdk"));
  } catch (err) {
    throw new Error(
      "Claude Agent SDK is not available. Run npm install in this skill folder or from an environment with @anthropic-ai/claude-agent-sdk installed.\n" +
        String(err?.message || err)
    );
  }
  const prompt = `You are designing an adversarial rubric for a Paperclip literature-consensus workflow.

Return JSON only. No markdown.

Context:
- A novokine is a secreted bivalent minibinder that activates/clusters two cell-surface proteins.
- The workflow must decide literature-only activation direction and high/mid/small novokine likelihood.
- Do NOT use Open Targets, DE, expression direction, GWAS, or co-expression to decide activation direction.
- Every accepted evidence claim must be Paperclip-verifiable.
- First run or simulate a 10-agent adversarial design panel. These design agents must design the rubric itself, not merely review outputs after the fact.
- The returned JSON must include exactly 10 rubric_design_agents with design_principle, required_fields, decision_rules, failure_tests, acceptance_standard, and rubric_contribution.
- The returned JSON must also define exactly 10 adversarial_agents for runtime consensus review. Each runtime agent must stress-test a distinct failure mode.
- Keep the schema_version as novokine-adversarial-rubric-v1 and rubric_owner as claude-agent-sdk.

Existing rubric:
${JSON.stringify(current, null, 2)}`;

  let text = "";
  for await (const message of query({
    prompt,
    options: {
      cwd: skillRoot,
      tools: [],
      disallowedTools: ["Bash", "Edit", "Write", "Read"],
      maxTurns: 1,
      jsonSchema,
      permissionMode: "dontAsk"
    }
  })) {
    if (message.type === "assistant") {
      for (const block of message.message.content) {
        if (block.type === "text") text += block.text;
      }
    }
  }
  return JSON.parse(text.trim());
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return usage();

  const current = await readRubric(args.input);
  validateRubric(current);

  if (args.mode === "dry-run") {
    console.log(JSON.stringify({
      ok: true,
      mode: "dry-run",
      design_agents: current.rubric_design_agents.length,
      runtime_agents: current.adversarial_agents.length
    }, null, 2));
    return;
  }

  if (args.mode === "render-md") {
    await fs.writeFile(rubricMdPath, renderMarkdown(current));
    console.log(JSON.stringify({ ok: true, mode: "render-md", path: rubricMdPath }, null, 2));
    return;
  }

  const next = await generateWithClaude(current);
  validateRubric(next);
  await fs.writeFile(rubricPath, `${JSON.stringify(next, null, 2)}\n`);
  await fs.writeFile(rubricMdPath, renderMarkdown(next));
  console.log(JSON.stringify({
    ok: true,
    mode: "write",
    design_agents: next.rubric_design_agents.length,
    runtime_agents: next.adversarial_agents.length,
    path: rubricPath
  }, null, 2));
}

main().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
