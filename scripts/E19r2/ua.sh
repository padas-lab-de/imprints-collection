H=${1:-albek.co}
echo "$(hostname) $H"
curl -s -o /dev/null -w "UA Mozilla/5.0: %{http_code}\n" -A "Mozilla/5.0" --max-time 20 https://$H/
sleep 15
curl -s -o /dev/null -w "UA browser: %{http_code}\n" -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36" -H "Accept: text/html,application/xhtml+xml" -H "Accept-Language: de-DE,de;q=0.9" --max-time 20 https://$H/
