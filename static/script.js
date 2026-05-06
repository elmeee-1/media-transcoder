valid = false

function form(event) {
    download()

    if (!valid) {
        event.preventDefault()
        console.log("Blocked submit")
    }
    else {
        event.preventDefault()
        console.log("submit successfully")
    }
}

function download() {
    let input = document.getElementById("search")
    let url = input.value

    if (!url.includes("https://")) {
        valid = false
        alert("link must contain (https://) !")
        document.querySelector(".infos").style.display = "none"
        return
    }

    valid = true

    let brand_italic = input.previousElementSibling

    let hostname = url.split("//")[1].split("/")[0]
    let website_name = hostname.replace("www.", "").split(".")[0]

    document.querySelector(".infos").style.display = "flex"

    brand_italic.className = ""
    brand_italic.classList.add("fa-brands")
    brand_italic.classList.add(`fa-${website_name}`)

}



function clearInput() {
    document.getElementById("search").value = ""
    document.getElementById("search").focus()
}