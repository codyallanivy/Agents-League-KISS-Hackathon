import { FileManager } from './fileManager';
import * as path from 'path';

export interface Decision {
  id: string;
  date: string;
  title: string;
  why: string;
  status: 'active' | 'parked' | 'revisited' | 'closed';
}

export class DecisionManager {
  private fileManager: FileManager;
  private decisionsFile: string;

  constructor(fileManager: FileManager) {
    this.fileManager = fileManager;
    this.decisionsFile = path.join(process.cwd(), 'DECISIONS.md');
  }

  getAllDecisions(): Decision[] {
    const content = this.fileManager.readFile(this.decisionsFile);
    return this.parseDecisions(content);
  }

  getRecentDecisions(count: number): Decision[] {
    return this.getAllDecisions().slice(-count);
  }

  logDecision(decision: Omit<Decision, 'id'>): void {
    const decisions = this.getAllDecisions();
    const newId = String((decisions.length || 0) + 1).padStart(3, '0');
    const fullDecision: Decision = { ...decision, id: newId };

    const entry = `\n## D-${newId}\n` +
      `- **Date:** ${fullDecision.date}\n` +
      `- **Title:** ${fullDecision.title}\n` +
      `- **Why:** ${fullDecision.why}\n` +
      `- **Status:** ${fullDecision.status}\n`;

    this.fileManager.appendFile(this.decisionsFile, entry);
  }

  private parseDecisions(content: string): Decision[] {
    const decisions: Decision[] = [];
    const sections = content.split('## D-');

    for (let i = 1; i < sections.length; i++) {
      const section = sections[i];
      const id = section.split('\n')[0];
      const lines = section.split('\n');

      const decision: Decision = {
        id,
        date: this.extractValue(lines, 'Date') || new Date().toISOString().split('T')[0],
        title: this.extractValue(lines, 'Title') || 'Untitled',
        why: this.extractValue(lines, 'Why') || '',
        status: (this.extractValue(lines, 'Status') as any) || 'active',
      };

      decisions.push(decision);
    }

    return decisions;
  }

  private extractValue(lines: string[], key: string): string | null {
    for (const line of lines) {
      if (line.includes(key)) {
        return line.split('**').pop()?.trim() || null;
      }
    }
    return null;
  }
}
