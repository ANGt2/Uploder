export PATH=$PATH:$HOME/bin

# دستور کلش (حالا به فایل مخصوص خودش متصل شده و خودکار عمل میکند)
alias update-vpn='cd ~/barry_test && curl -Lo clash.yaml https://raw.githubusercontent.com/Delta-Kronecker/V2ray-Config/main/config/clash.yaml && python clash_convert.py'

# دستور کانفیگ‌های معمولی (که از تو اسم فایل را میپرسد)
alias v2update='cd ~/barry_test && python convert.py'
