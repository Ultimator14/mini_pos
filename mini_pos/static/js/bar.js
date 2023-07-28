let myTimer = setInterval(updateBarBody, 3000);

async function updateBarBody() {
    let server_status_div = document.getElementById("server-status");

    try {
        const response = await fetch("/fetch/bar");
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
