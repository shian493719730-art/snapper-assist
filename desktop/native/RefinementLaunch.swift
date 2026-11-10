import Foundation

/// A selected-text edit is not a coding project. Give the CLI an empty profile
/// for this invocation, with only a link to the existing login file. In
/// particular, neither ~/.codex/skills nor ~/.agents/skills may be discovered:
/// both support symlinks into protected Documents folders on macOS.
struct RefinementLaunch {
    static let executable = URL(fileURLWithPath: "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex")
    static let settings = [
        "project_doc_max_bytes=0", "project_doc_fallback_filenames=[]",
        "skills.bundled.enabled=false", "skills.include_instructions=false",
        "features.skip_host_skill_discovery=true", "features.plugins=false",
        "features.plugin_discovery_prefetch=false", "features.remote_plugin=false",
        "features.apps=false", "features.hooks=false", "features.workspace_dependencies=false",
        "features.skill_search=false", "features.shell_tool=false", "features.unified_exec=false",
        "features.code_mode_host=false", "features.browser_use=false",
        "features.browser_use_external=false", "features.computer_use=false",
        "features.multi_agent=false", "features.view_image=false",
        "web_search=\"disabled\"", "model_reasoning_effort=\"low\""
    ]
    static var configArguments: [String] { settings.flatMap { ["-c", $0] } }
    static func arguments(schema: URL, output: URL) -> [String] {
        ["exec", "--ephemeral", "--ignore-user-config", "--sandbox", "read-only", "--skip-git-repo-check"]
            + configArguments + ["--output-schema", schema.path, "-o", output.path, "-"]
    }

    enum LaunchError: Error { case savedLoginUnavailable }

    static func environment(directory: URL, inherited: [String: String] = ProcessInfo.processInfo.environment,
                            userDirectory: URL = FileManager.default.homeDirectoryForCurrentUser) throws -> [String: String] {
        let fm = FileManager.default
        let existingHome = inherited["CODEX_HOME"].map { URL(fileURLWithPath: $0, isDirectory: true) }
            ?? userDirectory.appendingPathComponent(".codex", isDirectory: true)
        let auth = existingHome.appendingPathComponent("auth.json")
        guard fm.fileExists(atPath: auth.path) else { throw LaunchError.savedLoginUnavailable }
        let profile = directory.appendingPathComponent("profile", isDirectory: true)
        let codex = profile.appendingPathComponent(".codex", isDirectory: true)
        try fm.createDirectory(at: codex, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        try fm.setAttributes([.posixPermissions: 0o700], ofItemAtPath: profile.path)
        // Do not read, serialize, or copy credentials. The tested CLI preserves
        // this symlink on auth writes, so refreshes keep using the same login.
        try fm.createSymbolicLink(at: codex.appendingPathComponent("auth.json"), withDestinationURL: auth)
        var env = inherited
        for key in ["OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"] { env.removeValue(forKey: key) }
        // These are the child's real profile/config locations, not changes to
        // the user's shell, global config, projects or installed skills.
        env["HOME"] = profile.path; env["CODEX_HOME"] = codex.path
        return env
    }
}
