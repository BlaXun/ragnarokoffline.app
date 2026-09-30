//! `ragnarok-stack export-table <name>`: one of the server's tables as the
//! running server sees it, for the tools in Settings -> Tools (#195).
//!
//! The base table is read out of the map container (it lives in the image),
//! and the mods' `db/import` copy (state/modbuild/db, which is what the
//! container mounts there) is laid over it the way rAthena does: an entry
//! whose `Id` already exists has the fields it names replaced, and a new `Id`
//! is added. So a mod's monster or item shows up in the tools, and a mod's
//! change to a stock one does too.
//!
//! Field-level at the top of each entry only. rAthena merges some nested
//! lists more finely than that, but a tool showing a mod's `Drops:` list in
//! place of the stock one is the useful answer.

use crate::config::Config;
use crate::docker::Docker;
use std::fs;

/// The tables a tool may ask for: names, not paths, so nothing else in the
/// container can be read through this.
pub const TABLES: &[&str] = &["mob_db", "item_db_equip", "item_db_etc", "item_db_usable"];

pub fn export_table(cfg: &Config, dk: &Docker, name: &str) -> Result<String, String> {
    if !TABLES.contains(&name) {
        return Err(format!("unknown table {name}; one of {}", TABLES.join(", ")));
    }
    let era = if crate::cmds::is_prerenewal(cfg) { "pre-re" } else { "re" };
    let base = dk
        .output(["exec", "ragnarok-map", "cat", &format!("/rathena/db/{era}/{name}.yml")])
        .map_err(|_| "The game server is not running. Press Play in Ragnarok Offline, then try again.".to_string())?;
    let import = fs::read_to_string(cfg.state.join("modbuild").join("db").join(format!("{name}.yml"))).ok();
    Ok(match import {
        Some(overlay) => overlay_entries(&base, &overlay),
        None => base,
    })
}

/// One `  - Id: N` entry: its first line, then (key, lines) blocks for each
/// top-level field, in order.
struct Entry {
    id: Option<String>,
    head: String,
    fields: Vec<(String, Vec<String>)>,
}

/// Split an rAthena YAML table into what comes before its entries, the
/// entries, and what comes after them (the `Footer:`).
fn split(text: &str) -> (Vec<String>, Vec<Entry>, Vec<String>) {
    let mut head = Vec::new();
    let mut entries: Vec<Entry> = Vec::new();
    let mut foot = Vec::new();
    let mut in_body = false;
    let mut in_foot = false;
    for line in text.lines() {
        if in_foot {
            foot.push(line.to_string());
            continue;
        }
        if !in_body {
            head.push(line.to_string());
            if line.trim_end() == "Body:" {
                in_body = true;
            }
            continue;
        }
        if !line.starts_with(' ') && !line.trim().is_empty() && !line.starts_with('#') {
            // A top-level key after the body: the footer and everything below.
            in_foot = true;
            foot.push(line.to_string());
            continue;
        }
        if let Some(rest) = line.strip_prefix("  - ") {
            let id = rest.strip_prefix("Id:").map(|v| v.trim().to_string());
            entries.push(Entry { id, head: line.to_string(), fields: Vec::new() });
            continue;
        }
        let Some(entry) = entries.last_mut() else {
            head.push(line.to_string());
            continue;
        };
        let is_field = line.starts_with("    ")
            && !line.starts_with("     ")
            && line.trim_start().split_once(':').is_some()
            && !line.trim_start().starts_with('-')
            && !line.trim_start().starts_with('#');
        if is_field {
            let key = line.trim_start().split(':').next().unwrap_or("").to_string();
            entry.fields.push((key, vec![line.to_string()]));
        } else if let Some((_, lines)) = entry.fields.last_mut() {
            lines.push(line.to_string());
        } else {
            // A comment or blank line straight after the entry's first line.
            entry.fields.push((String::new(), vec![line.to_string()]));
        }
    }
    (head, entries, foot)
}

/// `base` with `overlay`'s entries laid over it, as rAthena reads an import.
pub fn overlay_entries(base: &str, overlay: &str) -> String {
    let (head, mut entries, foot) = split(base);
    let (_, extra, _) = split(overlay);
    for add in extra {
        let found = add.id.as_ref().and_then(|id| entries.iter_mut().find(|e| e.id.as_ref() == Some(id)));
        match found {
            Some(entry) => {
                for (key, lines) in add.fields {
                    if key.is_empty() {
                        continue;
                    }
                    match entry.fields.iter_mut().find(|(k, _)| *k == key) {
                        Some(slot) => slot.1 = lines,
                        None => entry.fields.push((key, lines)),
                    }
                }
            }
            None => entries.push(add),
        }
    }
    let mut out = String::new();
    for line in &head {
        out.push_str(line);
        out.push('\n');
    }
    for entry in &entries {
        out.push_str(&entry.head);
        out.push('\n');
        for (_, lines) in &entry.fields {
            for line in lines {
                out.push_str(line);
                out.push('\n');
            }
        }
    }
    for line in &foot {
        out.push_str(line);
        out.push('\n');
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    const BASE: &str = "Header:\n  Type: MOB_DB\n  Version: 4\n\nBody:\n  - Id: 1002\n    AegisName: PORING\n    Name: Poring\n    Level: 1\n    Drops:\n      - Item: Jellopy\n        Rate: 7000\n  - Id: 1113\n    AegisName: DROPS\n    Name: Drops\n    Level: 2\n\nFooter:\n  Imports:\n  - Path: db/re/mob_db.yml\n";

    #[test]
    fn a_mod_changes_a_stock_entry_field_by_field_and_adds_its_own() {
        let overlay = "Header:\n  Type: MOB_DB\n  Version: 4\n\nBody:\n  - Id: 1002\n    Level: 99\n    Drops:\n      - Item: Apple\n        Rate: 100\n  - Id: 30001\n    AegisName: ISLAND_CRAB\n    Name: Island Crab\n    Level: 5\n";
        let out = overlay_entries(BASE, overlay);
        // The Poring keeps its name, takes the mod's level and drops.
        let poring = &out[out.find("Id: 1002").unwrap()..out.find("Id: 1113").unwrap()];
        assert!(poring.contains("Name: Poring") && poring.contains("Level: 99") && poring.contains("Item: Apple"), "{poring}");
        assert!(!poring.contains("Jellopy") && !poring.contains("Level: 1\n"), "{poring}");
        // Untouched entries and the mod's new one are there; the footer stays last.
        assert!(out.contains("Name: Drops") && out.contains("Name: Island Crab"), "{out}");
        assert!(out.trim_end().ends_with("- Path: db/re/mob_db.yml"), "{out}");
        assert!(out.find("Island Crab").unwrap() < out.find("Footer:").unwrap());
    }

    #[test]
    fn with_nothing_to_lay_over_the_table_is_unchanged() {
        assert_eq!(overlay_entries(BASE, "Header:\n  Type: MOB_DB\n"), BASE);
    }

    #[test]
    fn only_the_listed_tables_can_be_asked_for() {
        assert!(TABLES.contains(&"mob_db"));
        assert!(!TABLES.iter().any(|t| t.contains('/') || t.contains('.')));
    }
}
