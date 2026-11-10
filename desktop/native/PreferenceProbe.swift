import Foundation

// Pure data path: no app UI, accessibility, login, tools or model invocation.
@main struct PreferenceProbe {
    static func main() throws {
        let args = CommandLine.arguments
        guard (3...4).contains(args.count), let catalog = RecipeCatalog.decode(try Data(contentsOf: URL(fileURLWithPath: args[1]))) else {
            fputs("usage: preference-probe catalog.json cases.json [knowledge.json]\n", stderr); exit(2)
        }
        let methodKnowledge = args.count == 4 ? try JSONDecoder().decode(MethodKnowledge.self, from: Data(contentsOf: URL(fileURLWithPath: args[3]))) : knowledge()
        let cases = try JSONDecoder().decode([String].self, from: Data(contentsOf: URL(fileURLWithPath: args[2])))
        let output = cases.map { text -> [String: Any] in
            let p = preparePrompt(text, catalog: catalog)
            return ["original":p.original, "recipe":p.recipeID, "text":p.text, "questions":p.questions,
                    "ai_payload_contains_prepared_draft":enhancementPrompt(p).contains("prepared_draft"),
                    "problem_preferences":problemSolvingPreferences(p),
                    "method_ids":refinementMethods(p, bundle:methodKnowledge).map(\.id),
                    "revision":p.revision]
        }
        FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]))
    }
}
