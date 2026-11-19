using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

[assembly: AssemblyTitle("局中事")]
[assembly: AssemblyProduct("局中事")]

internal sealed class Launcher : Form
{
    private readonly Label status;
    private readonly Button open;
    private readonly System.Windows.Forms.Timer monitor;
    private readonly EventWaitHandle activate;
    private Process engine;
    private Uri session;
    private bool closing;

    private Launcher(EventWaitHandle activate)
    {
        this.activate = activate;
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
                string folder = AppDomain.CurrentDomain.BaseDirectory;
                var start = new ProcessStartInfo {
                    FileName = Path.Combine(folder, "runtime", "python.exe"),
                    WorkingDirectory = folder,
                    Arguments = @"-X utf8 -B -u game\main.py --desktop --assets game\frontend\dist",
                    UseShellExecute = false, CreateNoWindow = true,
                    RedirectStandardInput = true, RedirectStandardOutput = true,
                    RedirectStandardError = true
                };
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

    [STAThread]
    private static void Main()
    {
        string profile = Environment.GetEnvironmentVariable("JUZHONGSHI_DATA_DIR");
        if (String.IsNullOrEmpty(profile))
            profile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "局中事");
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
                Application.Run(new Launcher(activate));
            } finally {
                mutex.ReleaseMutex();
            }
        }
    }
}
