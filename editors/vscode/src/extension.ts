import * as path from 'path';
import {
  commands,
  ExtensionContext,
  Terminal,
  window,
  workspace,
} from 'vscode';
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from 'vscode-languageclient/node';

let client: LanguageClient | undefined;
let novaTerminal: Terminal | undefined;

/** Resolve the configured `nova` executable path, expanding
 * `${workspaceFolder}` and relative paths against the first workspace. */
function toolchainPath(): string {
  const raw = workspace
    .getConfiguration('nova')
    .get<string>('toolchainPath', 'nova')
    .trim();
  const root = workspace.workspaceFolders?.[0]?.uri.fsPath;
  let resolved = raw;
  if (root) {
    resolved = resolved.replace(/\$\{workspaceFolder\}/g, root);
  }
  // A bare command name (no separator) stays as-is so PATH lookup works;
  // an explicit relative path is resolved against the workspace root.
  if (resolved.includes('/') && !path.isAbsolute(resolved) && root) {
    resolved = path.join(root, resolved);
  }
  return resolved;
}

/** Run `nova <subcommand> <file>` in a dedicated integrated terminal. */
function runInTerminal(subcommand: string): void {
  const editor = window.activeTextEditor;
  if (!editor || editor.document.languageId !== 'nova') {
    window.showWarningMessage('NOVA: open a .nova file first.');
    return;
  }
  const file = editor.document.uri.fsPath;
  const cwd = workspace.getWorkspaceFolder(editor.document.uri)?.uri.fsPath
    ?? path.dirname(file);

  if (!novaTerminal || novaTerminal.exitStatus !== undefined) {
    novaTerminal = window.createTerminal({ name: 'NOVA', cwd });
  }
  novaTerminal.show(true);
  // Quote the paths for the shell.
  const nova = toolchainPath();
  novaTerminal.sendText(`${quote(nova)} ${subcommand} ${quote(file)}`);
}

function quote(s: string): string {
  return /[^\w./-]/.test(s) ? `'${s.replace(/'/g, `'\\''`)}'` : s;
}

function startLanguageServer(context: ExtensionContext): void {
  const enabled = workspace
    .getConfiguration('nova')
    .get<boolean>('languageServer.enabled', true);
  if (!enabled) {
    return;
  }

  const serverOptions: ServerOptions = {
    command: toolchainPath(),
    args: ['lsp'],
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: 'file', language: 'nova' }],
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher('**/*.nova'),
    },
    // The server is minimal; a failed start should not spam the user.
    outputChannelName: 'NOVA Language Server',
  };

  client = new LanguageClient(
    'novaLanguageServer',
    'NOVA Language Server',
    serverOptions,
    clientOptions,
  );

  client.start().catch((err) => {
    window.showWarningMessage(
      `NOVA: could not start the language server (${err}). ` +
        'Syntax highlighting still works. Check `nova.toolchainPath`.',
    );
  });
}

export function activate(context: ExtensionContext): void {
  context.subscriptions.push(
    commands.registerCommand('nova.check', () => runInTerminal('check')),
    commands.registerCommand('nova.run', () => runInTerminal('run')),
    commands.registerCommand('nova.build', () => runInTerminal('build')),
    commands.registerCommand('nova.fmt', () => runInTerminal('fmt')),
    commands.registerCommand('nova.lint', () => runInTerminal('lint')),
    commands.registerCommand('nova.restartServer', async () => {
      await client?.stop();
      client = undefined;
      startLanguageServer(context);
    }),
  );

  startLanguageServer(context);
}

export function deactivate(): Thenable<void> | undefined {
  return client?.stop();
}
