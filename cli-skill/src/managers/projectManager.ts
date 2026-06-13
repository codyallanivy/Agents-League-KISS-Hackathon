import { FileManager } from './fileManager';
import * as path from 'path';

export interface ProjectState {
  projectName: string;
  sprintGoal: string;
  status: 'active' | 'paused' | 'complete';
  tier: '1' | '2' | '3';
  createdAt: string;
  lastUpdatedAt: string;
}

export class ProjectManager {
  private fileManager: FileManager;
  private projectDir: string = process.cwd();

  constructor(fileManager: FileManager) {
    this.fileManager = fileManager;
  }

  async initializeProject(projectName: string): Promise<void> {
    const projectDir = path.join(this.projectDir, projectName);
    this.fileManager.ensureDir(projectDir);
    this.fileManager.ensureDir(path.join(projectDir, 'agile'));

    // Create PROJECT_STATE.md
    const projectState: ProjectState = {
      projectName,
      sprintGoal: 'TBD - set your first sprint goal',
      status: 'active',
      tier: '1',
      createdAt: new Date().toISOString(),
      lastUpdatedAt: new Date().toISOString(),
    };
    
    this.fileManager.writeFile(
      path.join(projectDir, 'PROJECT_STATE.md'),
      this.getProjectStateTemplate(projectState)
    );

    // Create DECISIONS.md
    this.fileManager.writeFile(
      path.join(projectDir, 'DECISIONS.md'),
      this.getDecisionsTemplate()
    );

    // Create TODO.md
    this.fileManager.writeFile(
      path.join(projectDir, 'TODO.md'),
      this.getTodoTemplate()
    );

    // Create ITERATION_LOG.md
    this.fileManager.writeFile(
      path.join(projectDir, 'ITERATION_LOG.md'),
      this.getIterationLogTemplate()
    );

    // Create AGENT_CONTEXT.md
    this.fileManager.writeFile(
      path.join(projectDir, 'AGENT_CONTEXT.md'),
      this.getAgentContextTemplate()
    );

    // Create BRAND_VOICE.md
    this.fileManager.writeFile(
      path.join(projectDir, 'BRAND_VOICE.md'),
      this.getBrandVoiceTemplate()
    );

    // Create RISK_POLICY.md
    this.fileManager.writeFile(
      path.join(projectDir, 'RISK_POLICY.md'),
      this.getRiskPolicyTemplate()
    );

    // Create agile/PRODUCT_VISION.md
    this.fileManager.writeFile(
      path.join(projectDir, 'agile', 'PRODUCT_VISION.md'),
      this.getProductVisionTemplate()
    );
  }

  loadProjectState(): ProjectState | null {
    const filePath = path.join(this.projectDir, 'PROJECT_STATE.md');
    if (!this.fileManager.fileExists(filePath)) {
      return null;
    }
    
    // Parse markdown to extract JSON-like data
    const content = this.fileManager.readFile(filePath);
    // Simple parsing - in production would use proper markdown parser
    return {
      projectName: this.extractField(content, 'projectName') || 'Unknown',
      sprintGoal: this.extractField(content, 'sprintGoal') || 'TBD',
      status: 'active',
      tier: '1',
      createdAt: new Date().toISOString(),
      lastUpdatedAt: new Date().toISOString(),
    };
  }

  async checkScope(request: string): Promise<{ isInScope: boolean; tier: string; suggestion: string }> {
    const tier2Keywords = ['enterprise', 'sso', 'advanced analytics', 'team', 'role-based', 'custom'];
    const tier3Keywords = ['massive scale', 'global', 'saas platform', 'white label'];
    
    const lowerRequest = request.toLowerCase();
    
    for (const keyword of tier3Keywords) {
      if (lowerRequest.includes(keyword)) {
        return {
          isInScope: false,
          tier: '3 (Vision)',
          suggestion: `This feature is Tier 3 (vision-only). Let's focus on Tier 1 (core product) first.`,
        };
      }
    }

    for (const keyword of tier2Keywords) {
      if (lowerRequest.includes(keyword)) {
        return {
          isInScope: false,
          tier: '2 (Future)',
          suggestion: `This feature is Tier 2 (post-launch). Adding to DECISIONS.md as a parked idea.\nLet's nail Tier 1 first.`,
        };
      }
    }

    return {
      isInScope: true,
      tier: '1 (Current)',
      suggestion: `This is in scope for v1.`,
    };
  }

  async completeIteration(iterationNum: number): Promise<void> {
    const filePath = path.join(this.projectDir, 'ITERATION_LOG.md');
    const timestamp = new Date().toISOString();
    
    const entry = `\n## Iteration ${iterationNum}\nCompleted at: ${timestamp}\nStatus: COMPLETE\n`;
    this.fileManager.appendFile(filePath, entry);
  }

  async generateSummary(): Promise<string> {
    let summary = '✓ Work Completed\n';
    summary += '  - Task 1: Done\n';
    summary += '  - Task 2: Done\n\n';
    
    summary += '◐ Blocked Items\n';
    summary += '  - None\n\n';
    
    summary += '✎ Decisions Made\n';
    summary += '  - D-001: Set project scope\n\n';
    
    summary += '→ Next Best Task\n';
    summary += '  - Define sprint 1 deliverables\n\n';
    
    summary += `Confidence: 85%\n`;
    
    return summary;
  }

  async extractBrandVoice(url: string): Promise<Record<string, string>> {
    // Simple mock - in production would fetch and parse
    return {
      style: 'Warm, professional',
      tone: 'Friendly, helpful',
      values: 'Quality, reliability',
    };
  }

  private extractField(content: string, field: string): string | null {
    const regex = new RegExp(`${field}[:\\s]+([^\\n]+)`);
    const match = content.match(regex);
    return match ? match[1].trim() : null;
  }

  private getProjectStateTemplate(state: ProjectState): string {
    return `# Project State

**Project Name:** ${state.projectName}
**Status:** ${state.status}
**Tier:** ${state.tier}
**Created:** ${state.createdAt}
**Last Updated:** ${state.lastUpdatedAt}

## Current Sprint
**Goal:** ${state.sprintGoal}
**Status:** In progress

## Summary
- Tasks Done: 0
- Tasks Blocked: 0
- Decisions: 0

_Update this file after each session._
`;
  }

  private getDecisionsTemplate(): string {
    return `# Decisions

Log every significant decision with timestamp, why, and revisit trigger.

## Format
- **D-XXX** | Date | Title | Why | Status | Revisit

---

_No decisions logged yet. Add your first one!_
`;
  }

  private getTodoTemplate(): string {
    return `# To Do

## Current Sprint

- [ ] Item 1 | light | D-XXX
- [ ] Item 2 | medium | D-XXX

## Status
- [ ] Not started: 2
- [x] Done: 0
- [~] Blocked: 0

_Use [x] to mark done, [~] for blocked._
`;
  }

  private getIterationLogTemplate(): string {
    return `# Iteration Log

Track completed work, decisions, and confidence scores.

---

_No iterations logged yet._
`;
  }

  private getAgentContextTemplate(): string {
    return `# Agent Context

Updated: ${new Date().toISOString()}

## Current Agent
None yet

## Last Agent's Work
None yet

## Open Questions
None yet
`;
  }

  private getBrandVoiceTemplate(): string {
    return `# Brand Voice

_Not yet defined. Run: kiss brand-update <your-website-url>_
`;
  }

  private getRiskPolicyTemplate(): string {
    return `# Risk Policy

## Scope-Creep Stop Condition
**STOP and ask before doing any of the following:**
- Building anything for Tier 2/3 beyond documenting it
- Adding a new product feature not in agile/PRODUCT_VISION v1
- Expanding scope with new capabilities before launch

## Default Rule
Default answer to "should we also build X?" is: **"capture it in vision, don't build it."**

## Agent Authority
- Client (you) makes final decisions
- Agent recommends, then defers
- Silence is never approval
`;
  }

  private getProductVisionTemplate(): string {
    return `# Product Vision

## Tier 1 (Current - v1 Launch)
- [ ] Core feature 1
- [ ] Core feature 2
- [ ] Core feature 3

## Tier 2 (Future - Post-launch)
- [ ] Advanced feature 1
- [ ] Advanced feature 2

## Tier 3 (Vision - Long-term)
- [ ] Enterprise feature 1
- [ ] Enterprise feature 2
`;
  }
}
