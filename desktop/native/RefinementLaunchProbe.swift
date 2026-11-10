// Integration-test driver, not linked into the app. Emits launch metadata only;
// never starts a model turn and never reads or prints a credential.
import Foundation

@main struct RefinementLaunchProbe {
    static func main() throws {
        guard CommandLine.arguments.count == 2 else { exit(2) }
        let dir = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let env = try RefinementLaunch.environment(directory: dir)
        let object: [String: Any] = ["executable": RefinementLaunch.executable.path,
            "execArguments": RefinementLaunch.arguments(schema: dir.appendingPathComponent("schema.json"), output: dir.appendingPathComponent("result.json")),
            "configArguments": RefinementLaunch.configArguments,
            "profile": env["HOME"]!, "codexHome": env["CODEX_HOME"]!]
        print(String(data: try JSONSerialization.data(withJSONObject: object), encoding: .utf8)!)
    }
}
