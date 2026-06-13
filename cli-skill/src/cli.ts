import chalk from 'chalk';
import * as fs from 'fs';
import * as path from 'path';
import { FileManager } from './managers/fileManager';
import { ProjectManager } from './managers/projectManager';
import { DecisionManager } from './managers/decisionManager';
import { TodoManager } from './managers/todoManager';

export class KissCLI {
  private fileManager: FileManager;
  private projectManager: ProjectManager;
  private decisionManager: DecisionManager;
  private todoManager: TodoManager;

  constructor() {
    this.fileManager = new FileManager();
    this.projectManager = new ProjectManager(this.fileManager);
    this.decisionManager = new DecisionManager(this.fileManager);
    this.todoManager = new TodoManager(this.fileManager);
  }

  async run(args: string[]): Promise<void> {
    const [command, ...commandArgs] = args;

    if (!command || command === '--help' || command === '-h') {
      this.showHelp();
      return;
    }

    switch (command) {
      case 'init':
        await this.handleInit(commandArgs);
        break;
      case 'status':
        await this.handleStatus(commandArgs);
        break;
      case 'request':
        await this.handleRequest(commandArgs);
        break;
      case 'done':
        await this.handleDone(commandArgs);
        break;
      case 'complete-iteration':
        await this.handleCompleteIteration(commandArgs);
        break;
      case 'summarize':
        await this.handleSummarize(commandArgs);
        break;
      case 'decisions':
        await this.handleDecisions(commandArgs);
        break;
      case 'brand-update':
        await this.handleBrandUpdate(commandArgs);
        break;
      default:
        console.log(chalk.red(`✗ Unknown command: ${command}`));
        this.showHelp();
        process.exit(1);
    }
  }

  private async handleInit(args: string[]): Promise<void> {
    const projectName = args[0] || 'my-project';
    console.log(chalk.blue(`\n🎯 Initializing KISS Project: ${projectName}\n`));
    
    await this.projectManager.initializeProject(projectName);
    
    console.log(chalk.green(`✓ Project initialized at: ./${projectName}`));
    console.log(chalk.dim('\nNext steps:\n') + 
      `  1. ${chalk.yellow('kiss status')} - View project status\n` +
      `  2. ${chalk.yellow('kiss request "<feature>"')} - Add work\n` +
      `  3. ${chalk.yellow('kiss done <task-id>')} - Mark tasks complete\n`);
  }

  private async handleStatus(_args: string[]): Promise<void> {
    const state = this.projectManager.loadProjectState();
    
    if (!state) {
      console.log(chalk.red('✗ No project found. Run: kiss init <project-name>'));
      return;
    }

    console.log(chalk.blue(`\n═══════════════════════════════════════\n`));
    console.log(chalk.bold(`Project: ${state.projectName}`));
    console.log(chalk.bold(`Sprint Goal: ${state.sprintGoal}`));
    console.log(chalk.dim(`Status: ${state.status}\n`));

    // Show recent decisions
    const decisions = this.decisionManager.getRecentDecisions(3);
    if (decisions.length > 0) {
      console.log(chalk.yellow('Recent Decisions:'));
      decisions.forEach(d => {
        console.log(`  ${chalk.cyan(`D-${d.id}`)}: ${d.title}`);
      });
      console.log('');
    }

    // Show TODO summary
    const todos = this.todoManager.getTodoSummary();
    console.log(chalk.yellow('Todo Summary:'));
    console.log(`  Done: ${chalk.green(todos.done)} | ` +
      `Todo: ${chalk.cyan(todos.todo)} | ` +
      `Blocked: ${chalk.red(todos.blocked)}`);

    console.log(chalk.blue(`\n═══════════════════════════════════════\n`));
  }

  private async handleRequest(args: string[]): Promise<void> {
    const request = args.join(' ');
    if (!request) {
      console.log(chalk.red('✗ Please provide a feature request'));
      return;
    }

    console.log(chalk.blue(`\n🔍 Checking scope against RISK_POLICY...\n`));
    
    const { isInScope, tier, suggestion } = await this.projectManager.checkScope(request);
    
    if (!isInScope) {
      console.log(chalk.red(`✗ Out of scope (${tier} feature)\n`));
      console.log(chalk.dim(suggestion));
      console.log(chalk.green(`\n✓ Added to DECISIONS.md as "Parked Idea"`));
    } else {
      console.log(chalk.green(`✓ In scope (Tier ${tier})\n`));
      console.log(chalk.dim('Add this to TODO.md and get building!'));
    }
  }

  private async handleDone(args: string[]): Promise<void> {
    const taskId = args[0];
    if (!taskId) {
      console.log(chalk.red('✗ Please provide a task ID'));
      return;
    }

    await this.todoManager.markTaskDone(taskId);
    console.log(chalk.green(`✓ Task ${taskId} marked done`));
  }

  private async handleCompleteIteration(args: string[]): Promise<void> {
    const iterationNum = args[0];
    if (!iterationNum) {
      console.log(chalk.red('✗ Please provide an iteration number'));
      return;
    }

    await this.projectManager.completeIteration(parseInt(iterationNum));
    console.log(chalk.green(`✓ Iteration ${iterationNum} marked complete`));
  }

  private async handleSummarize(_args: string[]): Promise<void> {
    console.log(chalk.blue(`\n═══════════════════════════════════════\n`));
    console.log(chalk.bold('Session Summary'));
    console.log(chalk.blue(`═══════════════════════════════════════\n`));

    const summary = await this.projectManager.generateSummary();
    console.log(summary);

    console.log(chalk.blue(`═══════════════════════════════════════\n`));
  }

  private async handleDecisions(_args: string[]): Promise<void> {
    const decisions = this.decisionManager.getAllDecisions();
    
    console.log(chalk.blue(`\n═══════════════════════════════════════`));
    console.log(chalk.bold(`All Decisions (${decisions.length})`));
    console.log(chalk.blue(`═══════════════════════════════════════\n`));

    decisions.forEach((d, i) => {
      console.log(`${chalk.cyan(`D-${d.id}`)} | ${chalk.dim(d.date)} | ${d.title}`);
      console.log(`  Why: ${d.why}`);
      console.log(`  Status: ${d.status}\n`);
    });
  }

  private async handleBrandUpdate(args: string[]): Promise<void> {
    const url = args[0];
    if (!url) {
      console.log(chalk.red('✗ Please provide a URL'));
      return;
    }

    console.log(chalk.blue(`\n🎨 Extracting brand voice from ${url}...\n`));
    
    const brandVoice = await this.projectManager.extractBrandVoice(url);
    console.log(chalk.green('✓ Brand voice updated'));
    console.log(chalk.dim(`\nExtracted:\n${JSON.stringify(brandVoice, null, 2)}`));
  }

  private showHelp(): void {
    console.log(chalk.blue(`
╔═══════════════════════════════════════════════════════════╗
║  KISS Agile Operator CLI — Keep It Simple Studio         ║
║  Copilot-integrated project memory system                ║
╚═══════════════════════════════════════════════════════════╝

${chalk.bold('COMMANDS:')}

  ${chalk.cyan('kiss init <project-name>')}
    Initialize a new KISS project with all memory files

  ${chalk.cyan('kiss status')}
    Show project state, recent decisions, and todo summary

  ${chalk.cyan('kiss request "<feature>"')}
    Request a feature (checks scope against RISK_POLICY)

  ${chalk.cyan('kiss done <task-id>')}
    Mark a todo item as complete

  ${chalk.cyan('kiss complete-iteration <number>')}
    Mark an entire iteration as complete

  ${chalk.cyan('kiss summarize')}
    Generate session summary (work, decisions, blockers)

  ${chalk.cyan('kiss decisions')}
    View all logged decisions

  ${chalk.cyan('kiss brand-update <url>')}
    Extract brand voice from website/social media

  ${chalk.cyan('kiss --help')}
    Show this help message

${chalk.bold('PHILOSOPHY:')}
  Not anti-AI. Anti-waste.
  Build what matters. Keep your context. Track your decisions.
  Your project stays yours.

`));
  }
}
