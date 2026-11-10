import Foundation
import CryptoKit

struct MethodChoice: Decodable {
    let id, title: String
    let recipe: PromptRecipe
}
struct MethodChoiceDomain: Decodable {
    let id, title, recipe_id, default_method, example: String
    let methods: [MethodChoice]
    var suggested: MethodChoice? { methods.first { $0.id == default_method } }
}
struct MethodChoiceCatalog: Decodable {
    let schema_version: Int
    let revision: String
    let domains: [MethodChoiceDomain]
    static func decode(_ data: Data) -> MethodChoiceCatalog? {
        guard let value = try? JSONDecoder().decode(Self.self, from: data), value.schema_version == 1,
              !value.domains.isEmpty, value.domains.count < 20,
              Set(value.domains.map(\.id)).count == value.domains.count,
              Set(value.domains.map(\.recipe_id)).count == value.domains.count,
              value.domains.allSatisfy({ d in
                  !d.id.isEmpty && !d.title.isEmpty && d.recipe_id != "general" && d.suggested != nil &&
                  !d.methods.isEmpty && Set(d.methods.map(\.id)).count == d.methods.count &&
                  d.methods.allSatisfy { !$0.id.isEmpty && !$0.title.isEmpty && $0.recipe.id == d.recipe_id && $0.recipe.isValid }
              }) else { return nil }
        return value
    }
    static var bundled: MethodChoiceCatalog? {
        guard let url = Bundle.main.url(forResource: "domain-presets", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return decode(data)
    }
}

/// Plain method IDs only. Preserve unrelated profile metadata and manual feedback.
struct DomainPreferenceState {
    var object: [String: Any]
    static var url: URL {
        if Bundle.main.bundleIdentifier == "local.snapper.assist.preview" {
            return FileManager.default.temporaryDirectory.appendingPathComponent("snapper-assist-preview-0.8/domain-preferences.json")
        }
        return FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".codex/agent-learning-loop/domain-preferences.json")
    }
    static func load(from url: URL = Self.url) throws -> Self {
        guard FileManager.default.fileExists(atPath: url.path) else {
            return Self(object: ["schema_version": 1, "preferences": [String: Any](), "feedback": [String: Any]()])
        }
        guard let object = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as? [String: Any],
              object["schema_version"] as? Int == 1, object["preferences"] is [String: Any], object["feedback"] is [String: Any] else {
            throw MethodPreferenceError.invalidProfile
        }
        return Self(object: object)
    }
    func selectedMethod(_ domain: String) -> String? {
        guard let values = object["preferences"] as? [String: Any], let row = values[domain] as? [String: Any],
              row["status"] as? String == "confirmed" else { return nil }
        return row["method"] as? String
    }
    mutating func choose(domain: MethodChoiceDomain, method: String?) throws {
        guard method == nil || domain.methods.contains(where: { $0.id == method }) else { throw MethodPreferenceError.unavailableMethod }
        var values = object["preferences"] as? [String: Any] ?? [:]
        var follows = object["app_follow_suggestions"] as? [String: Bool] ?? [:]
        if let method {
            values[domain.id] = ["method": method, "status": "confirmed", "origin": "explicit-user", "updated_at": ISO8601DateFormatter().string(from: Date())]
            follows.removeValue(forKey: domain.id)
        } else {
            values.removeValue(forKey: domain.id); follows[domain.id] = true
        }
        object["preferences"] = values; object["app_follow_suggestions"] = follows
    }
    func save(to url: URL = Self.url) throws {
        let fm = FileManager.default
        try fm.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        let temp = url.deletingLastPathComponent().appendingPathComponent(".method-" + UUID().uuidString)
        defer { try? fm.removeItem(at: temp) }
        let data = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys, .prettyPrinted])
        guard fm.createFile(atPath: temp.path, contents: data, attributes: [.posixPermissions: 0o600]) else { throw MethodPreferenceError.saveFailed }
        let file = try FileHandle(forWritingTo: temp); try file.synchronize(); try file.close()
        guard rename(temp.path, url.path) == 0 else { throw MethodPreferenceError.saveFailed }
    }
    func applying(to base: RecipeCatalog, choices: MethodChoiceCatalog) throws -> RecipeCatalog {
        var recipes = base.recipes
        let follows = object["app_follow_suggestions"] as? [String: Bool] ?? [:]
        for domain in choices.domains {
            let selected = selectedMethod(domain.id)
            guard selected != nil || follows[domain.id] == true else { continue }
            guard let method = domain.methods.first(where: { $0.id == (selected ?? domain.default_method) }) else { throw MethodPreferenceError.unavailableMethod }
            let value = method.recipe
            let title = value.title + (selected == nil ? "·建议" : "")
            let recipe = PromptRecipe(id: value.id, title: title, intent: value.intent, keywords: value.keywords,
                                      deliverables: value.deliverables, checks: value.checks, questions: value.questions, source_ids: value.source_ids)
            if let index = recipes.firstIndex(where: { $0.id == domain.recipe_id }) {
                // Already compiled by the host: retain its newer source and local edits.
                if recipes[index].title != title { recipes[index] = recipe }
            } else { recipes.insert(recipe, at: 0) }
        }
        guard recipes.count <= 20 else { throw MethodPreferenceError.catalogLimit }
        let identity = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        let digest = SHA256.hash(data: identity + Data(choices.revision.utf8)).map { String(format: "%02x", $0) }.joined().prefix(12)
        return RecipeCatalog(schema_version: 1, revision: base.revision + "-prefs-" + digest, recipes: recipes)
    }
}
enum MethodPreferenceError: Error, LocalizedError {
    case invalidProfile, unavailableMethod, saveFailed, catalogLimit
    var errorDescription: String? {
        switch self {
        case .invalidProfile: return "偏好数据无法读取；已保留原文件与当前方法。"
        case .unavailableMethod: return "此偏好需要更新的方法数据；已保留当前方法。"
        case .saveFailed: return "偏好未能保存；当前方法保持不变。"
        case .catalogLimit: return "当前本地方法数量超过适配范围；已保留原配置。"
        }
    }
}
