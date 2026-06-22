use reqwest::Client;

pub async fn alert(webhook: &str, level: &str, msg: &str) {
    if webhook.is_empty() {
        return;
    }
    let payload = serde_json::json!({
        "level": level,
        "message": msg
    });
    let _ = Client::new().post(webhook).json(&payload).send().await;
}
