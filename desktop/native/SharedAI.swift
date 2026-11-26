import Foundation
import Security

struct SharedAIStatus: Decodable {
    let mode: String
    let provider_configured: Bool
    let label: String
    let expires: Double
    let remaining_requests: Int
    let daily_limit: Int
    let budget_micros_cny: Int
    let used_micros_cny: Int
    var summary: String {
        let state = mode == "enabled" ? "共享 AI 已连接" : "邀请码已连接 · 真实模型扣费未开启"
        return state + "\n剩余次数：\(remaining_requests) · 每日上限：\(daily_limit)\n额度：\(String(format: "%.2f", Double(budget_micros_cny) / 1_000_000)) 元，已用 \(String(format: "%.2f", Double(used_micros_cny) / 1_000_000)) 元\n有效期：" + Date(timeIntervalSince1970: expires / 1000).formatted(date: .abbreviated, time: .omitted)
    }
}
struct SharedAIResult: Decodable {
    struct Method: Decodable { let title, reason: String }
    let suggestion: GeneratedSuggestion
    let methods: [Method]
}
enum SharedAIError: Error, LocalizedError {
    case missingInvite, keychain(OSStatus), service(String), invalidResponse
    var errorDescription: String? {
        switch self {
        case .missingInvite: return "请先在“共享 AI 与邀请码”中输入邀请码。"
        case .keychain: return "无法保存邀请码，请检查系统钥匙串提示后重试。"
        case .invalidResponse: return "共享服务结果不完整，原文没有修改。"
        case .service(let code):
            return ["billing_disabled": "邀请码已连接；维护者尚未开启真实模型扣费。本地草稿可继续使用。",
                    "quota_or_request_limit": "已达到总额度、个人额度或使用次数上限。",
                    "invite_expired_or_revoked": "邀请码已过期或被撤销，请联系维护者。",
                    "invite_already_bound": "邀请码已在另一台设备使用，请联系维护者换一个。",
                    "invite_device_mismatch": "当前设备与邀请码不匹配，请重新连接或联系维护者。",
                    "invalid_invite": "邀请码无效，请核对后重试。",
                    "request_already_started": "该请求已开始处理，为避免重复扣费没有再次发送。",
                    "provider_not_configured": "维护者尚未完成模型连接，本地草稿仍可使用。",
                    "storage_not_ready": "共享服务尚未完成初始化，请稍后重试。",
                    "pricing_not_configured": "维护者尚未确认模型计价，暂不发送收费请求。"] [code] ?? "共享 AI 暂时未完成，请稍后重试；原文没有修改。"
        }
    }
}
enum SharedAI {
    static let origin = URL(string: "https://snapper-assist-shared-ai.shian493719370.chatgpt.site")!
    static let service = "local.snapper.assist.shared-ai"
    static func validCode(_ code: String) -> Bool { code.range(of: "^sa1_[a-f0-9]{64}$", options: .regularExpression) != nil }
    static func deviceID() -> String {
        if let id = UserDefaults.standard.string(forKey: "shared-ai-device-id") { return id }
        let id = UUID().uuidString; UserDefaults.standard.set(id, forKey: "shared-ai-device-id"); return id
    }
    static func savedCode() -> String? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service,
                                  kSecAttrAccount as String: "invitation", kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
    static func saveCode(_ code: String) throws {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: "invitation"]
        let data = Data(code.utf8)
        let updated = SecItemUpdate(query as CFDictionary, [kSecValueData as String: data] as CFDictionary)
        if updated == errSecSuccess { return }
        guard updated == errSecItemNotFound else { throw SharedAIError.keychain(updated) }
        var item = query; item[kSecValueData as String] = data
        item[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        let added = SecItemAdd(item as CFDictionary, nil); guard added == errSecSuccess else { throw SharedAIError.keychain(added) }
    }
    static func forgetCode() {
        SecItemDelete([kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: "invitation"] as CFDictionary)
    }
    static func request(_ path: String, code: String, body: [String: Any]? = nil) throws -> URLRequest {
        guard validCode(code), path.hasPrefix("/api/") else { throw SharedAIError.missingInvite }
        var req = URLRequest(url: origin.appendingPathComponent(String(path.dropFirst())), timeoutInterval: 190)
        req.httpMethod = body == nil ? "GET" : "POST"
        req.setValue("Bearer " + code, forHTTPHeaderField: "Authorization")
        req.setValue(deviceID(), forHTTPHeaderField: "X-Snapper-Device")
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body { req.httpBody = try JSONSerialization.data(withJSONObject: body) }
        return req
    }
    static func send<T: Decodable>(_ request: URLRequest, as: T.Type) async throws -> T {
        let session = URLSession(configuration: .ephemeral, delegate: NoRedirects(), delegateQueue: nil)
        defer { session.invalidateAndCancel() }
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse else { throw SharedAIError.invalidResponse }
        guard response.statusCode == 200 || response.statusCode == 201 else {
            let code = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["error"] as? String ?? "unavailable"
            throw SharedAIError.service(code)
        }
        guard data.count < 150000, let value = try? JSONDecoder().decode(T.self, from: data) else { throw SharedAIError.invalidResponse }
        return value
    }
    static func activate(_ code: String) async throws -> SharedAIStatus {
        let result = try await send(request("/api/activate", code: code, body: ["code": code]), as: SharedAIStatus.self)
        try saveCode(code); return result
    }
    static func status(_ code: String) async throws -> SharedAIStatus { try await send(request("/api/status", code: code), as: SharedAIStatus.self) }
    static func refine(_ original: String, code: String) async throws -> SharedAIResult {
        let info = try await status(code)
        guard info.mode == "enabled" else { throw SharedAIError.service("billing_disabled") }
        let value = try await send(request("/api/refine", code: code, body: ["original": original, "preferences": RefinementSkills.explicitPreferences(), "request_id": UUID().uuidString]), as: SharedAIResult.self)
        guard let encoded = try? JSONEncoder().encode(value.suggestion), GeneratedSuggestion.parse(encoded) != nil else { throw SharedAIError.invalidResponse }
        return value
    }
}
final class NoRedirects: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) { completionHandler(nil) }
}
