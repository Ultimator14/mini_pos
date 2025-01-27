function startBarUpdate(name) {
    let myTimer = setInterval(() => updateBarBody(name), 3000);
}

async function updateBarBody(name) {
    let server_status_div = document.getElementById("server-status");

    try {
        const response = await fetch("/fetch/bar/" + name);
        document.getElementsByTagName('body')[0].innerHTML = await response.text();

        server_status_div.classList.remove("server-status-down");
        server_status_div.classList.add("server-status-up");
        server_status_div.innerHTML = "Server is up";

    } catch (error) {
        server_status_div.classList.remove("server-status-up");
        server_status_div.classList.add("server-status-down");
        server_status_div.innerHTML = "Server is down";
    }
}
