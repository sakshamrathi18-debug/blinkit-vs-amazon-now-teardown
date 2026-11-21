# source this: helpers for repeated navigation. Usage: S=scenario; amz_now_open; bl_open
Q=./qc
amz_now_open(){ $Q cold-open --app amazon --scenario $S --screen "Amazon home ($S start)" 2>&1 | head -1
  $Q tap-text --app amazon --scenario $S --exact "close" --wait 2 >/dev/null 2>&1
  $Q tap-text --app amazon --scenario $S --exact "Now" --wait 4 >/dev/null 2>&1
  out=$($Q capture --app amazon --scenario $S --screen "Amazon Now landing ($S)" 2>&1 | head -1); echo "$out"
  case "$out" in *thin*) $Q tap 540 1110 --app amazon --scenario $S --wait 3 >/dev/null 2>&1; echo "closed popup";; esac; }
bl_open(){ $Q cold-open --app blinkit --scenario $S --screen "Blinkit home ($S start)" 2>&1 | head -1; }
dump_text(){ id=$(ls -t data/text | head -1); cut -d'|' -f2 data/text/$id; }
