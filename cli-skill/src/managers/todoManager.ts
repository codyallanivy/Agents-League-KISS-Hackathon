import { FileManager } from './fileManager';
import * as path from 'path';

export interface TodoItem {
  id: string;
  title: string;
  status: 'todo' | 'done' | 'blocked';
  weight: 'light' | 'medium' | 'heavy' | 'super-heavy';
  relatedDecision?: string;
}

export class TodoManager {
  private fileManager: FileManager;
  private todoFile: string;

  constructor(fileManager: FileManager) {
    this.fileManager = fileManager;
    this.todoFile = path.join(process.cwd(), 'TODO.md');
  }

  getTodoSummary(): { done: number; todo: number; blocked: number } {
    const content = this.fileManager.readFile(this.todoFile);
    const doneCount = (content.match(/\[x\]/g) || []).length;
    const todoCount = (content.match(/\[ \]/g) || []).length;
    const blockedCount = (content.match(/\[~\]/g) || []).length;

    return { done: doneCount, todo: todoCount, blocked: blockedCount };
  }

  async markTaskDone(taskId: string): Promise<void> {
    const content = this.fileManager.readFile(this.todoFile);
    const updated = content.replace(
      new RegExp(`- \\[ \\] ${taskId}`, 'g'),
      `- [x] ${taskId}`
    );
    this.fileManager.writeFile(this.todoFile, updated);
  }

  addTodo(item: TodoItem): void {
    const checkbox = item.status === 'done' ? '[x]' : 
                     item.status === 'blocked' ? '[~]' : '[ ]';
    
    const entry = `\n- ${checkbox} ${item.title} | ${item.weight}` +
                  (item.relatedDecision ? ` | ${item.relatedDecision}` : '') + '\n';
    
    this.fileManager.appendFile(this.todoFile, entry);
  }

  private parseItems(content: string): TodoItem[] {
    const items: TodoItem[] = [];
    const lines = content.split('\n');
    let itemId = 1;

    for (const line of lines) {
      if (line.includes('[') && (line.includes('[ ]') || line.includes('[x]') || line.includes('[~]'))) {
        const status = line.includes('[x]') ? 'done' : line.includes('[~]') ? 'blocked' : 'todo';
        const parts = line.split('|');
        const title = parts[0].replace(/^.*\]\s+/, '').trim();
        const weight = (parts[1]?.trim() || 'medium') as any;

        items.push({
          id: String(itemId++),
          title,
          status,
          weight,
        });
      }
    }

    return items;
  }
}
