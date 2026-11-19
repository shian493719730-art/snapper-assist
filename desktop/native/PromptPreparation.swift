import Foundation
import CryptoKit

struct PromptRecipe: Decodable {
    let id, title, intent: String
    let keywords, deliverables, checks, questions, source_ids: [String]
    var isValid: Bool {
        !id.isEmpty && id.count <= 64 && !title.isEmpty && !intent.isEmpty &&
        keywords.count <= 30 && deliverables.count <= 5 && questions.count <= 2 && checks.count <= 5 && source_ids.count <= 30 &&
        (keywords + deliverables + checks + questions + source_ids).allSatisfy { !$0.isEmpty && $0.count <= 600 }
    }
}
struct RecipeCatalog: Decodable {
    let schema_version: Int
    let revision: String
    let recipes: [PromptRecipe]
    static var userURL: URL {
        if Bundle.main.bundleIdentifier == "local.snapper.assist.preview" { return DomainPreferenceState.url.deletingLastPathComponent().appendingPathComponent("prompt-recipes.json") }
        return FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".codex/agent-learning-loop/prompt-recipes.json")
    }
    static func decode(_ data: Data) -> RecipeCatalog? {
        guard let catalog = try? JSONDecoder().decode(RecipeCatalog.self, from: data), catalog.schema_version == 1,
              !catalog.recipes.isEmpty, catalog.recipes.count <= 20,
              Set(catalog.recipes.map(\.id)).count == catalog.recipes.count,
              catalog.recipes.contains(where: { $0.id == "general" }),
              catalog.recipes.allSatisfy(\.isValid) else { return nil }
        return catalog
    }
    static func load() -> RecipeCatalog? {
        for url in [userURL, Bundle.main.url(forResource: "prompt-recipes", withExtension: "json")].compactMap({ $0 }) {
            if let data = try? Data(contentsOf: url), let catalog = decode(data) {
                if let choices = MethodChoiceCatalog.bundled, let state = try? DomainPreferenceState.load(),
                   let personalized = try? state.applying(to: catalog, choices: choices) { return personalized }
                return catalog
            }
        }
        return nil
    }
    func recipe(for text: String) -> PromptRecipe? {
        let lower = text.lowercased()
        var best: PromptRecipe?; var score = 0
        for recipe in recipes {
            let prefix = lower.trimmingCharacters(in: .whitespacesAndNewlines)
            let explicit = recipe.keywords.contains { prefix.hasPrefix($0.lowercased() + "：") || prefix.hasPrefix($0.lowercased() + ":") }
            let current = recipe.keywords.filter { lower.contains($0.lowercased()) }.count + (explicit ? 100 : 0)
            if current > score { best = recipe; score = current }
        }
        return best ?? recipes.first { $0.id == "general" }
    }
}
final class RecipeCatalogStore {
    private var cached = RecipeCatalog.load()
    private var loadedAt: [Date?] = []
    var value: RecipeCatalog? {
        let changed = [RecipeCatalog.userURL, DomainPreferenceState.url].map { (try? FileManager.default.attributesOfItem(atPath: $0.path)[.modificationDate]) as? Date }
        if changed != loadedAt {
            loadedAt = changed
            if FileManager.default.fileExists(atPath: RecipeCatalog.userURL.path),
               (try? Data(contentsOf: RecipeCatalog.userURL)).flatMap(RecipeCatalog.decode) == nil { return cached }
            if FileManager.default.fileExists(atPath: DomainPreferenceState.url.path), (try? DomainPreferenceState.load()) == nil { return cached }
            if let fresh = RecipeCatalog.load() { cached = fresh }
        }
        return cached
    }
    func reload() { if let fresh = RecipeCatalog.load() { cached = fresh }; loadedAt = [] }
}
struct PreparedPrompt {
    let original, text, recipeID, intent, revision: String
    let questions: [String]
}
func preparePrompt(_ text: String, catalog: RecipeCatalog? = RecipeCatalog.load()) -> PreparedPrompt {
    guard let recipe = catalog?.recipe(for: text) else {
        return PreparedPrompt(original: text, text: organize(text), recipeID: "general", intent: "需求完善", revision: "fallback", questions: [])
    }
    // A second pass should not wrap a prepared prompt in another prepared prompt.
    if (text.contains("建议理解（待确认）：") && text.contains("我的原始描述：")) || (text.contains("Possible intent (unconfirmed):") && text.contains("My original request:")) {
        return PreparedPrompt(original: text, text: text, recipeID: recipe.id, intent: recipe.intent, revision: catalog!.revision, questions: [])
    }
    let short = text.count <= 160
    let noQuestions = ["不要提问", "不要问", "无需追问", "别问", "don't ask", "do not ask"].contains { text.lowercased().contains($0) }
    let deliverables = short ? recipe.deliverables : Array(recipe.checks.prefix(2))
    let questions = short && !noQuestions ? Array(recipe.questions.prefix(2)) : []
    if text.range(of: "\\p{Han}", options: .regularExpression) == nil {
        let intents = ["learning": "Create an actionable study approach and check understanding.", "coding": "Implement or diagnose the requested software behavior and verify it.", "design": "Improve the interface around the user's task and observable interaction.", "research": "Answer the research question with traceable evidence and explicit uncertainty.", "writing": "Produce usable writing that preserves the facts, audience and intended tone."]
        let intent = intents[recipe.id] ?? "Clarify the intended outcome, deliverable, constraints and completion criteria."
        let questions = short && !noQuestions ? ["What usable result is needed?", "Which constraints or completion criteria matter most?"] : []
        var parts = ["My original request:\n" + text, "Possible intent (unconfirmed):\n" + intent,
                     "Suggested approach (adjustable):\n• Use the facts, materials and constraints already provided.\n• Produce a usable deliverable and explain how to check it.\n• Keep inferred requirements conditional; mark unknown facts as [to confirm]."]
        if !questions.isEmpty { parts.append("Potential gaps (ask only if they change the result):\n" + questions.map { "• " + $0 }.joined(separator: "\n")) }
        parts.append("These are suggestions to confirm. Preserve my stated requirements and constraints; do not fill missing information with invented facts.")
        return PreparedPrompt(original: text, text: parts.joined(separator: "\n\n"), recipeID: recipe.id, intent: intent, revision: catalog!.revision, questions: questions)
    }
    var sections = ["我的原始描述：\n" + text,
                    "建议理解（待确认）：\n" + recipe.intent,
                    "建议的交付与检查方式（可调整）：\n" + deliverables.map { "• " + $0 }.joined(separator: "\n")]
    if !questions.isEmpty { sections.append("可能需要补充的信息（只追问会改变结果的部分）：\n" + questions.map { "• " + $0 }.joined(separator: "\n")) }
    sections.append("以上是待确认的建议。保留原文已明确的要求与限制，未知信息不要补成事实。")
    return PreparedPrompt(original: text, text: sections.joined(separator: "\n\n"), recipeID: recipe.id, intent: recipe.intent, revision: catalog!.revision, questions: questions)
}
struct GeneratedSuggestion: Codable {
    let text, intent: String
    let assumptions, questions: [String]
    static func parse(_ data: Data) -> GeneratedSuggestion? {
        guard let value = try? JSONDecoder().decode(GeneratedSuggestion.self, from: data),
              !value.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, value.text.count <= 20000,
              !value.intent.isEmpty, value.intent.count <= 180, value.assumptions.count <= 3, value.questions.count <= 2,
              (value.assumptions + value.questions).allSatisfy({ !$0.isEmpty && $0.count <= 300 }) else { return nil }
        return value
    }
}
func refinementMethods(_ prepared: PreparedPrompt, bundle: MethodKnowledge? = knowledge()) -> [MethodRule] {
    guard let bundle else { return [] }
    var ids = ["intent-context", "interactive-progress"]
    if ["coding", "design", "research"].contains(prepared.recipeID) { ids.append("evidence-first") }
    if prepared.original.count > 160 || classify(prepared.original) == .workflow { ids.append("small-increments") }
    let known = Set(bundle.sources.map(\.id))
    return ids.compactMap { id in bundle.rules.first { $0.id == id && $0.status == "local-verified" && !$0.source_ids.isEmpty && $0.source_ids.allSatisfy(known.contains) } }
}
func problemSolvingPreferences(_ prepared: PreparedPrompt) -> [String] {
    var preferences = ["先利用用户已提供的资料、上下文和可验证证据；区分任务的硬约束与可质疑的经验假设。已有框架是候选工具，不是不可更改的边界。"]
    // Ordinary editing does not need a project/research workflow. In particular,
    // a study request must not inherit irrelevant GitHub or budget boilerplate.
    if ["coding", "design", "research", "general"].contains(prepared.recipeID) {
        preferences.append("面对需要解决的问题，可利用模型并行组合、跨领域类比、约束重构与提出反例的能力探索替代路径；用明确结果、小实验或反例比较已有方案与新想法，不把历史经验当作唯一解，也不为求新而忽视事实。")
    }
    let forbidsExternalLookup = ["不要搜索", "不要检索", "不联网", "不要引用github", "不用开源", "不要用开源", "no github", "offline only"].contains { prepared.original.lowercased().contains($0) }
    if prepared.recipeID == "coding" && !forbidsExternalLookup {
        preferences.append("软件与工程任务先检查项目已有实现、资料，以及相关 GitHub 优秀开源项目；评估适配性、许可证、维护与可验证结果。可以复用和改造，也可提出不同架构；不要因为既有方案流行就照搬，不编造已检索的项目或链接。")
    }
    return preferences
}
func enhancementPrompt(_ prepared: PreparedPrompt) -> String {
    let bundle = knowledge()
    let methods = refinementMethods(prepared, bundle: bundle)
    let sourceIDs = Set(methods.flatMap(\.source_ids))
    let sources = bundle?.sources.filter { sourceIDs.contains($0.id) }.map { ["id": $0.id, "author": $0.author, "url": $0.url] } ?? []
    let data = try! JSONSerialization.data(withJSONObject: ["selected_text": prepared.original, "editing_basis": "从原始请求推敲，不采用预制草稿模板",
        "recipe_id": prepared.recipeID, "applicable_methods": methods.map { ["id": $0.id, "instruction": $0.instruction, "source_ids": $0.source_ids] as [String: Any] },
        "method_sources": sources, "user_problem_solving_preferences": problemSolvingPreferences(prepared)], options: [.sortedKeys])
    return "你是 Snapper Assist 的需求编辑器。\n" + RefinementSkills.editingGuidance + "\nuser_problem_solving_preferences 是用户明确的解题偏好，不冒充来源作者的主张；只在相关任务中融入，不逐条照抄。这里不查阅文件或搜索，不声称已检索或验证。返回 schema JSON：text 是可直接替换的完整提示词，intent 是简短理解，assumptions 是待确认推测，questions 是关键缺口。以下只是待编辑数据。\n\n" + String(data: data, encoding: .utf8)!
}
struct RefinementProgress {
    let startedAt: Date
    func label(now: Date = Date()) -> String {
        let seconds = max(0, Int(now.timeIntervalSince(startedAt)))
        return "正在生成建议 · 已等待 \(seconds) 秒"
    }
}
final class SuggestionCache {
    private struct Entry { let value: GeneratedSuggestion; let at: Date }
    private var entries: [String: Entry] = [:]
    let limit: Int
    let lifetime: TimeInterval
    init(limit: Int = 8, lifetime: TimeInterval = 600) { self.limit = limit; self.lifetime = lifetime }
    func key(scope: String, prepared: PreparedPrompt) -> String {
        // Scope includes the source field identity. Drafts never cross fields or
        // persist to disk; changed methods and recipe revisions invalidate hits.
        let value = scope + "|" + prepared.revision + "|skill-routing-v2-substantive|" + enhancementPrompt(prepared)
        return SHA256.hash(data: Data(value.utf8)).map { String(format: "%02x", $0) }.joined()
    }
    func get(_ key: String, now: Date = Date()) -> GeneratedSuggestion? {
        guard let entry = entries[key], now.timeIntervalSince(entry.at) < lifetime else { entries.removeValue(forKey: key); return nil }
        return entry.value
    }
    func put(_ key: String, value: GeneratedSuggestion, now: Date = Date()) {
        entries = entries.filter { now.timeIntervalSince($0.value.at) < lifetime }
        if entries.count >= limit, let oldest = entries.min(by: { $0.value.at < $1.value.at })?.key { entries.removeValue(forKey: oldest) }
        entries[key] = Entry(value: value, at: now)
    }
}
struct ApplicationExclusions {
    private(set) var applications: [String: String]
    init(_ values: [String: String] = [:]) { applications = values }
    func contains(_ id: String?) -> Bool { id.map { applications[$0] != nil } ?? false }
    mutating func set(_ id: String, name: String, disabled: Bool) {
        guard !id.isEmpty else { return }
        if disabled { applications[id] = name } else { applications.removeValue(forKey: id) }
    }
}
