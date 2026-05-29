use std::collections::HashSet;

use tauri_plugin_opener::OpenerExt;

use crate::models::PackageInfo;
use crate::scanner::total_count;
use crate::storage;
use crate::now_minutes;

fn escape_html(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}

pub fn render_report(date: &str, packages: &[PackageInfo], total_unique: usize) -> String {
    let mut rows = String::new();
    for package in packages {
        rows.push_str(&format!(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
            escape_html(&package.manager),
            escape_html(&package.name),
            escape_html(&package.version),
            escape_html(&package.time)
        ));
    }

    if rows.is_empty() {
        rows = "<tr><td colspan=\"4\" class=\"empty\">今日暂无安装记录</td></tr>".to_string();
    }

    format!(
        r#"<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>包安装监控报告 - {date}</title>
  <style>
    body {{ margin: 0; background: #eef1f5; color: #1f2937; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px; }}
    header, section {{ background: #fff; border: 1px solid #dbe3ea; border-radius: 8px; margin-bottom: 16px; padding: 22px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .meta {{ color: #64748b; }}
    .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
    .stat {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
    .stat strong {{ display: block; font-size: 30px; margin-top: 6px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 12px; text-align: left; }}
    th {{ background: #f8fafc; color: #475569; }}
    .empty {{ color: #64748b; text-align: center; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>包安装监控报告</h1>
      <div class="meta">{date} | 生成时间: {generated_at}</div>
    </header>
    <section class="stats">
      <div class="stat">当日新增<strong>{package_count}</strong></div>
      <div class="stat">历史总数<strong>{total_unique}</strong></div>
      <div class="stat">包管理器<strong>{manager_count}</strong></div>
    </section>
    <section>
      <table>
        <thead>
          <tr><th>管理器</th><th>包名</th><th>版本</th><th>时间</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>"#,
        date = date,
        generated_at = now_minutes(),
        package_count = packages.len(),
        total_unique = total_unique,
        manager_count = packages
            .iter()
            .map(|p| p.manager.clone())
            .collect::<HashSet<_>>()
            .len(),
        rows = rows
    )
}

pub fn generate_report(app: &tauri::AppHandle, date: &str) -> Result<String, String> {
    let data = storage::load_storage()?;
    let packages = data.records.get(date).cloned().unwrap_or_default();
    let html = render_report(date, &packages, total_count(&data.records));
    let path = storage::reports_dir()?.join(format!("report_{}.html", date));

    std::fs::write(&path, html).map_err(|e| e.to_string())?;
    app.opener()
        .open_path(path.to_string_lossy().to_string(), None::<&str>)
        .map_err(|e| e.to_string())?;

    Ok(path.to_string_lossy().to_string())
}
