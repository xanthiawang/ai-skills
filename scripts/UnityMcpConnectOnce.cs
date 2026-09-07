// Optional one-shot recovery for MCP for Unity 10.2.0.
// Copy into a Unity project's Assets/Editor after installing the package.
using System;
using System.IO;
using System.Threading.Tasks;
using MCPForUnity.Editor.Services;
using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
public static class UnityMcpConnectOnce
{
    private const string Marker = "Library/CodexUnityMcpSetup.complete";
    private static readonly double Deadline;

    static UnityMcpConnectOnce()
    {
        if (Application.isBatchMode || AssetDatabase.IsAssetImportWorkerProcess()) return;
        try { if (File.Exists(Marker)) return; }
        catch (Exception e) { Debug.LogError("Unity MCP setup marker: " + e.Message); return; }
        Deadline = EditorApplication.timeSinceStartup + 120;
        EditorApplication.update += WaitUntilReady;
    }

    private static void WaitUntilReady()
    {
        if (EditorApplication.timeSinceStartup > Deadline)
        {
            EditorApplication.update -= WaitUntilReady;
            Debug.LogError("Unity MCP setup timed out waiting for an idle editor.");
            return;
        }
        if (EditorApplication.isCompiling || EditorApplication.isUpdating) return;
        EditorApplication.update -= WaitUntilReady;
        _ = ConnectAsync();
    }

    private static async Task ConnectAsync()
    {
        try
        {
            EditorPrefs.SetString("MCPForUnity.HttpUrl", "http://127.0.0.1:8080");
            EditorConfigurationCache.Instance.SetUseHttpTransport(true);
            EditorConfigurationCache.Instance.Refresh();
            for (int attempt = 0; attempt < 3; attempt++)
            {
                var bridge = MCPServiceLocator.Bridge;
                if (bridge.IsRunning || await bridge.StartAsync())
                {
                    var result = await bridge.VerifyAsync();
                    if (result.Success)
                    {
                        File.WriteAllText(Marker, DateTime.UtcNow.ToString("O") + "\n" + result.Message);
                        EditorPrefs.SetBool("MCPForUnity.AutoStartOnLoad", true);
                        Debug.Log("Unity MCP connected and verified: " + result.Message);
                        return;
                    }
                }
                await Task.Delay(1000);
            }
            Debug.LogError("Unity MCP setup failed: start the local HTTP server and retry after script reload.");
        }
        catch (Exception e) { Debug.LogError("Unity MCP setup failed: " + e); }
    }
}
