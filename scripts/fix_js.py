content = open("index.html", encoding="utf-8").read()
bad  = "function getLC(n){return LC[n]||hsl(,65%,60%);}"
good = "function getLC(n){var h=(n.split(\"\").reduce(function(a,c){return a+c.charCodeAt(0);},0)*37)%360;return LC[n]||(\"hsl(\"+h+\",65%,60%)\");}"
if bad in content:
    open("index.html","w",encoding="utf-8").write(content.replace(bad, good))
    print("PATCHED: getLC fixed")
else:
    lines = content.splitlines()
    print("Not found. Line 273:", repr(lines[272]))

