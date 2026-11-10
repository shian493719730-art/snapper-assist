import Foundation

/// Exercise only bundled public assets and temporary fixtures. No UI, account or model.
func runBundledMethodTests() {
    var count = 0
    func check(_ value: @autoclosure () -> Bool, _ label: String) {
        guard value() else { fputs("FAILED method bundle: \(label)\n", stderr); exit(1) }; count += 1
    }
    guard let choices = MethodChoiceCatalog.bundled,
          let url = Bundle.main.url(forResource: "prompt-recipes", withExtension: "json"),
          let data = try? Data(contentsOf: url), let base = RecipeCatalog.decode(data) else {
        fputs("Missing public method assets\n", stderr); exit(1)
    }
    let folder = FileManager.default.temporaryDirectory.appendingPathComponent("snapper-method-test-" + UUID().uuidString)
    let profile = folder.appendingPathComponent("domain-preferences.json")
    defer { try? FileManager.default.removeItem(at: folder) }
    do {
        let empty = try DomainPreferenceState.load(from: profile)
        check(choices.domains.count == 14 && base.recipes.count == 15, "fresh install includes 14 domains plus general")
        let plain = try empty.applying(to: base, choices: choices)
        check(!FileManager.default.fileExists(atPath: profile.path), "first load does not create a personal preference")
        check(plain.recipe(for: "学术讨论：什么算作知识？")?.title.contains("建议") == true, "public default is a suggestion")
        check(plain.recipe(for: "学术讨论：什么算作知识？")?.title.contains("苏式") == false, "no developer Socratic choice shipped as a universal preference")
        for domain in choices.domains {
            let original = (domain.id == "argument-review" ? "推敲我的观点：效率总是最重要的。" : domain.example) + "不要发送消息。"
            check(plain.recipe(for: original)?.id == domain.recipe_id, "fresh bundled route \(domain.id)")
            for method in domain.methods {
                var state = empty
                try state.choose(domain: domain, method: method.id)
                let personalized = try state.applying(to: base, choices: choices)
                let prepared = preparePrompt(original, catalog: personalized)
                check(prepared.recipeID == domain.recipe_id && prepared.text.contains(original) && prepared.text.contains(method.recipe.deliverables[0]), "native choice reaches prepared request \(domain.id)/\(method.id)")
            }
        }
        let academic = choices.domains.first { $0.id == "academic-dialogue" }!
        var state = empty; state.object["feedback"] = ["keep": ["accept": 2]]; state.object["unrelated"] = "preserve"
        try state.choose(domain: academic, method: "socratic-dialogue"); try state.save(to: profile)
        let restored = try DomainPreferenceState.load(from: profile)
        check(restored.selectedMethod(academic.id) == "socratic-dialogue" && restored.object["unrelated"] as? String == "preserve", "selection survives reload without losing unrelated metadata")
        check((restored.object["feedback"] as? [String: Any])?["keep"] != nil, "manual feedback preserved")
        let attributes = try FileManager.default.attributesOfItem(atPath: profile.path)
        check((attributes[.posixPermissions] as? NSNumber)?.intValue == 0o600, "private profile file permissions")
        let selected = try restored.applying(to: base, choices: choices)
        check(selected.revision != plain.revision, "changed method invalidates response cache key")
        let study = preparePrompt("期末复习第一章，不要问我问题。", catalog: selected)
        check(!study.text.contains("苏格拉底") && !study.text.contains("预算") && study.questions.isEmpty, "academic choice does not leak into study or override no-question instruction")
        try state.choose(domain: academic, method: nil)
        let reset = try state.applying(to: selected, choices: choices)
        check(reset.recipe(for: "学术讨论")?.title == academic.suggested!.recipe.title + "·建议", "reset overrides even a previously compiled personal recipe")
        check(state.selectedMethod(academic.id) == nil, "follow suggestion removes the personal choice")
        do { try state.choose(domain: academic, method: "not-installed"); check(false, "unknown choice") }
        catch { check(true, "unknown choice refused") }
        try Data("{broken".utf8).write(to: profile)
        do { _ = try DomainPreferenceState.load(from: profile); check(false, "corrupt profile") }
        catch { check((try? String(contentsOf: profile, encoding: .utf8)) == "{broken", "corrupt profile preserved rather than reset") }
        print("methods: \(count) bundled/fresh-profile checks passed; no model calls")
    } catch { fputs("FAILED method test: \(error)\n", stderr); exit(1) }
}
