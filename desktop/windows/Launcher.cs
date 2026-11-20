using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

[assembly: AssemblyTitle("局中事")]
[assembly: AssemblyProduct("局中事")]

internal sealed class Launcher : Form
{
    private const string Platform = "windows-x64";
    private static readonly string Package = AppDomain.CurrentDomain.BaseDirectory;
    private static readonly Regex VersionText = new Regex(@"\A(?:0|[1-9][0-9]{0,5})(?:\.(?:0|[1-9][0-9]{0,5})){2}\z");
    private readonly string profile;
    private readonly Label status;
    private readonly Button open;
    private readonly System.Windows.Forms.Timer monitor;
    private readonly EventWaitHandle activate;
    private Process engine;
    private Uri session;
    private bool closing;

    private Launcher(EventWaitHandle activate, string profile)
    {
        this.activate = activate;
        this.profile = profile;
        Text = "局中事";
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        Font = new Font("Microsoft YaHei UI", 10);
        AutoScaleMode = AutoScaleMode.Font;
        ClientSize = new Size(370, 145);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        status = new Label { Left = 22, Top = 22, Width = 325, Height = 52 };
        open = new Button { Text = "打开游戏", Left = 22, Top = 87, Width = 145, Height = 36 };
        var exit = new Button { Text = "退出游戏", Left = 190, Top = 87, Width = 145, Height = 36 };
        Controls.AddRange(new Control[] { status, open, exit });
        AcceptButton = open;
        open.Click += async delegate { await OpenGame(); };
        exit.Click += delegate { Close(); };
        Shown += async delegate { await OpenGame(); };
        FormClosing += delegate { closing = true; monitor.Stop(); StopEngine(); };
        monitor = new System.Windows.Forms.Timer { Interval = 400 };
        monitor.Tick += async delegate {
            if (engine != null && engine.HasExited && open.Enabled) {
                StopEngine();
                status.Text = "游戏已退出。点击“打开游戏”可重新启动。";
            }
            if (activate.WaitOne(0)) {
                WindowState = FormWindowState.Normal;
                Activate();
                if (open.Enabled) await OpenGame();
            }
        };
        monitor.Start();
    }

    private async Task OpenGame()
    {
        open.Enabled = false;
        try {
            if (session == null || engine == null || engine.HasExited) {
                StopEngine();
                status.Text = "正在启动《局中事》……";
                string folder = Package;
                var start = new ProcessStartInfo {
                    FileName = Path.Combine(folder, "runtime", "python.exe"),
                    WorkingDirectory = folder,
                    Arguments = @"-X utf8 -B -u game\main.py --desktop --assets game\frontend\dist",
                    UseShellExecute = false, CreateNoWindow = true,
                    RedirectStandardInput = true, RedirectStandardOutput = true,
                    RedirectStandardError = true
                };
                string version = ReadVersion(Path.Combine(folder, "VERSION"));
                if (version != null) {
                    start.EnvironmentVariables["JUZHONGSHI_UPDATE_PLATFORM"] = Platform;
                    start.EnvironmentVariables["JUZHONGSHI_UPDATE_VERSION"] = version;
                    start.EnvironmentVariables["JUZHONGSHI_UPDATE_ROOT"] = profile;
                }
                start.EnvironmentVariables["JUZHONGSHI_DATA_DIR"] = profile;
                engine = Process.Start(start);
                engine.BeginErrorReadLine();
                var line = engine.StandardOutput.ReadLineAsync();
                if (await Task.WhenAny(line, Task.Delay(60000)) != line)
                    throw new TimeoutException();
                Uri url;
                if (!Uri.TryCreate(await line, UriKind.Absolute, out url) ||
                    url.Scheme != "http" || url.Host != "127.0.0.1" || url.AbsolutePath != "/" ||
                    !url.Fragment.StartsWith("#session=", StringComparison.Ordinal))
                    throw new IOException();
                session = url;
            }
            try {
                Process.Start(new ProcessStartInfo(session.AbsoluteUri) { UseShellExecute = true });
                status.Text = "游戏已在浏览器打开。游玩期间请保留此窗口。";
            } catch (System.ComponentModel.Win32Exception) {
                status.Text = "无法打开浏览器。请设置 Windows 默认浏览器后点击“打开游戏”。";
            }
        } catch (Exception) {
            if (!closing) {
                StopEngine();
                status.Text = "启动失败。请确认已完整解压游戏，且当前账户可以保存文件。";
            }
        } finally {
            if (!closing) open.Enabled = true;
        }
    }

    private void StopEngine()
    {
        session = null;
        if (engine == null) return;
        try {
            if (!engine.HasExited) {
                engine.StandardInput.Close();
                if (!engine.WaitForExit(4500)) engine.Kill();
            }
        } catch (InvalidOperationException) {
            // The engine can finish between the exit check and closing its pipe.
        } catch (IOException) {
            if (!engine.HasExited) engine.Kill();
        } finally {
            engine.Dispose();
            engine = null;
        }
    }

    private static string ReadVersion(string path)
    {
        try {
            string value = File.ReadAllText(path).TrimEnd('\r', '\n');
            return VersionText.IsMatch(value) ? value : null;
        } catch (IOException) { return null; }
        catch (UnauthorizedAccessException) { return null; }
    }

    private static bool NonemptyFile(string path)
    {
        try {
            var item = new FileInfo(path);
            return item.Exists && item.Length > 0;
        } catch (IOException) { return false; }
        catch (UnauthorizedAccessException) { return false; }
    }

    private static bool TryUpdatedLaunch(string profile)
    {
        string updates = Path.Combine(profile, "updates");
        string next = ReadVersion(Path.Combine(updates, Platform + ".active"));
        string current = ReadVersion(Path.Combine(Package, "VERSION"));
        if (next == null || current == null || new Version(next) <= new Version(current)) return false;
        string folder = Path.Combine(updates, "versions", next, Platform);
        string exe = Path.Combine(folder, "局中事.exe");
        if (ReadVersion(Path.Combine(folder, "VERSION")) != next || !NonemptyFile(exe)
                || !NonemptyFile(Path.Combine(folder, "runtime", "python.exe"))
                || !NonemptyFile(Path.Combine(folder, "game", "main.py"))
                || !NonemptyFile(Path.Combine(folder, "game", "frontend", "dist", "index.html")))
            return false;
        try {
            var start = new ProcessStartInfo(exe) {
                WorkingDirectory = folder, UseShellExecute = false
            };
            start.EnvironmentVariables["JUZHONGSHI_DATA_DIR"] = profile;
            using (Process child = Process.Start(start)) { return child != null; }
        } catch (System.ComponentModel.Win32Exception) { return false; }
        catch (IOException) { return false; }
        catch (UnauthorizedAccessException) { return false; }
    }

    [STAThread]
    private static void Main()
    {
        string profile = Environment.GetEnvironmentVariable("JUZHONGSHI_DATA_DIR");
        if (String.IsNullOrEmpty(profile))
            profile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "局中事");
        profile = Path.GetFullPath(profile);
        if (TryUpdatedLaunch(profile)) return;
        string name;
        using (var hash = SHA256.Create()) {
            var bytes = Encoding.UTF8.GetBytes(Path.GetFullPath(profile).TrimEnd('\\').ToUpperInvariant());
            name = @"Local\Juzhongshi-" + BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-", "");
        }
        bool first;
        using (var activate = new EventWaitHandle(false, EventResetMode.AutoReset, name + "-open"))
        using (var mutex = new Mutex(true, name, out first)) {
            if (!first) { activate.Set(); return; }
            try {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new Launcher(activate, profile));
            } finally {
                mutex.ReleaseMutex();
            }
        }
    }
}
