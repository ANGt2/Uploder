#!/data/data/com.termux/files/usr/bin/bash
set -e

SESSION="bot"
PROJECT_DIR="$HOME/projects/bot"
CMD="python bot.py"

# اطمینان از وجود tmux session
tmux has-session -t "$SESSION" 2>/dev/null || tmux new -d -s "$SESSION"

# اگر داخل session از قبل bot.py در حال اجراست، دوباره اجرا نکن
if tmux capture-pane -pt "$SESSION" | tail -n 50 | grep -q "Bot"; then
  exit 0
fi

# اجرای ربات داخل tmux
tmux send-keys -t "$SESSION" "cd \"$PROJECT_DIR\" && $CMD" C-m

# جلوگیری از خواب (اختیاری ولی مفید)
termux-wake-lock 2>/dev/null || true
