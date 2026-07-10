use dither_core::{process, Settings};
use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Deserialize)]
struct Case {
    name: String,
    fixture: String,
    w: u32,
    h: u32,
    settings: Settings,
}

fn main() {
    let dir = std::env::args().nth(1).expect("dir");
    let want_name = std::env::args().nth(2).expect("case name e.g. case_12");
    let dir = Path::new(&dir);
    let index: Vec<Case> =
        serde_json::from_str(&fs::read_to_string(dir.join("index.json")).unwrap()).unwrap();
    let c = index.into_iter().find(|c| c.name == want_name).unwrap();
    println!("{} fixture={} algo={} {}x{}", c.name, c.fixture, c.settings.algorithm, c.w, c.h);

    let src = fs::read(dir.join(format!("{}_in.bin", c.name))).unwrap();
    let want = fs::read(dir.join(format!("{}_out.bin", c.name))).unwrap();
    let (got, _, _) = process(&src, c.w, c.h, &c.settings);

    let w = c.w as usize;
    let mut shown = 0;
    for i in 0..(got.len() / 4) {
        let g = &got[i * 4..i * 4 + 4];
        let wnt = &want[i * 4..i * 4 + 4];
        if g != wnt {
            let (x, y) = (i % w, i / w);
            println!("({:>2},{:>2}) got={:?} want={:?}", x, y, &g[..3], &wnt[..3]);
            shown += 1;
            if shown >= 24 {
                break;
            }
        }
    }
    if shown == 0 {
        println!("no mismatches");
    }
}
