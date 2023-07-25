let myTimer = setInterval(updateBarBody, 3000);

async function updateBarBody() {
    const response = await fetch("/fetch/bar");
    document.getElementsByTagName('body')[0].innerHTML = await response.text();
}
