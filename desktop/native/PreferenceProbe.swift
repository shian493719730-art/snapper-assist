import Foundation

// Pure data path: no app UI, accessibility, login, tools or model invocation.
@main struct PreferenceProbe {
    static func main() throws {
        let args = CommandLine.arguments
        guard args.count == 3, let catalog = RecipeCatalog.decode(try Data(contentsOf: URL(fileURLWithPath: args[1]))) else {
            fputs("usage: preference-probe catalog.json cases.json\n", stderr); exit(2)
        }
        let cases = try JSONDecoder().decode([String].self, from: Data(contentsOf: URL(fileURLWithPath: args[2])))
        let output = cases.map { text -> [String: Any] in
            let p = preparePrompt(text, catalog: catalog)
            return ["original":p.original, "recipe":p.recipeID, "text":p.text, "questions":p.questions,
                    "ai_payload_contains_prepared_draft":enhancementPrompt(p).contains("prepared_draft"),
                    "revision":p.revision]
        }
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]))
    }
}
