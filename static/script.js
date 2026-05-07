let currentJobId = null;
let pollInterval = null;

function handleForm(e) {
  e.preventDefault();
  download();
}

function download() {
  const input = document.getElementById("search");
  const url = input.value.trim();

  if (!url || !url.startsWith("http")) {
    showNotification("Please enter a valid URL", "error");
    document.getElementById("optionsSection").style.display = "none";
    return;
  }

  try {
    const icon = document.getElementById("brand-icon");
    const hostname = new URL(url).hostname.replace("www.", "");
    const name = hostname.split(".")[0];
    icon.className = `fab fa-${name}`;
  } catch (e) {

}

  document.getElementById("optionsSection").style.display = "block";
  document.getElementById("optionsSection").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearInput() {
  const input = document.getElementById("search");
  input.value = "";
  input.focus();
  document.getElementById("optionsSection").style.display = "none";
  document.getElementById("progressCard").style.display = "none";
  document.getElementById("brand-icon").className = "fab fa-youtube";
  if (pollInterval) clearInterval(pollInterval);
}

function showNotification(message, type = "info") {
  const toast = document.getElementById("toast");
  const msg = document.getElementById("toastMsg");
  const icon = toast.querySelector("i");

  msg.textContent = message;
  toast.className = "toast" + (type === "error" ? " error" : "");
  icon.className = type === "error" ? "fas fa-circle-xmark" : "fas fa-circle-info";

  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

async function startDownload(mediaType, quality) {
  const url = document.getElementById("search").value.trim();

  if (!url || !url.startsWith("http")) {
    showNotification("Please enter a valid URL first!", "error");
    return;
  }

  document.getElementById("optionsSection").style.display = "none";
  document.getElementById("progressCard").style.display = "block";

  document.getElementById("progressFill").style.width = "0%";
  document.getElementById("progressPercent").textContent = "0%";
  document.getElementById("statusText").textContent = "Starting download…";
  document.getElementById("statusDetail").textContent = "Initializing…";
  document.getElementById("saveBtn").style.display = "none";

  try {
    const response = await fetch("/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, media_type: mediaType, quality })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Download failed");
    }

    currentJobId = data.job_id;
    pollInterval = setInterval(checkStatus, 1000);
  } catch (error) {
    showNotification(error.message, "error");
    document.getElementById("statusText").textContent = "Error";
    document.getElementById("statusDetail").textContent = error.message;
    document.getElementById("progressCard").style.display = "block";
  }
}

async function checkStatus() {
  if (!currentJobId) return;

  try {
    const response = await fetch(`/status/${currentJobId}`);
    const data = await response.json();

    document.getElementById("progressFill").style.width = data.progress + "%";
    document.getElementById("progressPercent").textContent = data.progress + "%";

    if (data.status === "pending") {
      document.getElementById("statusText").textContent = "Pending…";
      document.getElementById("statusDetail").textContent = "Waiting to start…";
    } else if (data.status === "downloading") {
      document.getElementById("statusText").textContent = "Downloading…";
      document.getElementById("statusDetail").textContent = `Progress: ${data.progress}%`;
    } else if (data.status === "done") {
      clearInterval(pollInterval);
      document.getElementById("progressFill").style.width = "100%";
      document.getElementById("progressPercent").textContent = "100%";
      document.getElementById("statusText").textContent = "Download Complete!";
      document.getElementById("statusDetail").textContent = "Ready to save";
      document.getElementById("saveBtn").style.display = "flex";
    } else if (data.status === "error") {
      clearInterval(pollInterval);
      document.getElementById("statusText").textContent = "Download Failed";
      document.getElementById("statusDetail").textContent = data.error || "An error occurred";
    }
  } catch (error) {
    clearInterval(pollInterval);
    document.getElementById("statusText").textContent = "Connection Error";
    document.getElementById("statusDetail").textContent = "Failed to fetch status";
  }
}

function downloadFile() {
  if (!currentJobId) return;
  const link = document.createElement("a");
  link.href = `/file/${currentJobId}`;
  link.download = "";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

(function() {
  const canvas = document.createElement('canvas');
  canvas.id = 'network-canvas';
  canvas.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;';
  document.body.prepend(canvas);
  
  const ctx = canvas.getContext('2d');
  let W, H, dots = [];
  
  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  
  class Dot {
    constructor() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.r = Math.random() * 1.5 + 0.5;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > W) this.vx *= -1;
      if (this.y < 0 || this.y > H) this.vy *= -1;
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgb(200,0,0)';
      ctx.fill();
    }
  }
  
  function init() {
    resize();
    dots = Array.from({length: 40}, () => new Dot());
  }
  
  function animate() {
    ctx.clearRect(0, 0, W, H);
    dots.forEach(d => { d.update(); d.draw(); });
    
    for (let i = 0; i < dots.length; i++) {
      for (let j = i + 1; j < dots.length; j++) {
        const dx = dots[i].x - dots[j].x;
        const dy = dots[i].y - dots[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 150) {
          ctx.beginPath();
          ctx.moveTo(dots[i].x, dots[i].y);
          ctx.lineTo(dots[j].x, dots[j].y);
          ctx.strokeStyle = `rgb(80, 30, 30) `;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(animate);
  }
  
  init();
  animate();
  window.addEventListener('resize', init);
})();
