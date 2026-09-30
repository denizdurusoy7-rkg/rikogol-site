/* rikogol.com: click-to-play trailer, screenshot lightbox, language menu. No tracking, no cookies. */
(function () {
  "use strict";
  var doc = document;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Trailer: poster + big play button; the video only downloads after a click. */
  var shells = doc.querySelectorAll("[data-video]");
  Array.prototype.forEach.call(shells, function (shell) {
    var video = shell.querySelector("video");
    var button = shell.querySelector(".video-play");
    if (!video || !button) return;
    var start = function () {
      shell.classList.remove("has-overlay");
      button.hidden = true;
      video.controls = true;
      var p = video.play();
      if (p && p.catch) p.catch(function () {});
      video.focus();
    };
    button.hidden = false;
    video.controls = false;
    shell.classList.add("has-overlay");
    button.addEventListener("click", start);
    video.addEventListener("play", function () {
      shell.classList.remove("has-overlay");
      button.hidden = true;
      video.controls = true;
    });
    Array.prototype.forEach.call(doc.querySelectorAll("[data-play-trailer]"), function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        shell.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
        start();
      });
    });
  });

  /* Lightbox for the screenshot gallery (links still open the JPG without JS). */
  var dialog = doc.querySelector("[data-lightbox]");
  var links = doc.querySelectorAll("[data-gallery] a");
  if (dialog && links.length && typeof dialog.showModal === "function") {
    var stage = dialog.querySelector(".lb-stage");
    var img = doc.createElement("img");
    img.width = 1280;
    img.height = 720;
    img.decoding = "async";
    var caption = dialog.querySelector(".lb-caption");
    var count = dialog.querySelector(".lb-count");
    var full = dialog.querySelector(".lb-full");
    var index = 0;
    var opener = null;
    var show = function (n) {
      index = (n + links.length) % links.length;
      var link = links[index];
      var thumb = link.querySelector("img");
      img.alt = thumb.alt;
      img.src = link.getAttribute("data-large");
      if (!img.parentNode) stage.appendChild(img);
      caption.textContent = thumb.alt;
      count.textContent = index + 1 + " / " + links.length;
      full.href = link.href;
    };
    Array.prototype.forEach.call(links, function (link, n) {
      link.addEventListener("click", function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
        e.preventDefault();
        opener = link;
        show(n);
        dialog.showModal();
      });
    });
    dialog.addEventListener("click", function (e) {
      var action = e.target.closest ? e.target.closest("[data-lb]") : null;
      if (action) {
        var kind = action.getAttribute("data-lb");
        if (kind === "prev") show(index - 1);
        else if (kind === "next") show(index + 1);
        else dialog.close();
      } else if (e.target === dialog || e.target.classList.contains("lb-stage")) {
        dialog.close();
      }
    });
    dialog.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        show(index - 1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        show(index + 1);
      }
    });
    dialog.addEventListener("close", function () {
      if (img.parentNode) stage.removeChild(img);
      if (opener) opener.focus();
    });
    var startX = null;
    dialog.addEventListener("touchstart", function (e) {
      startX = e.touches[0].clientX;
    }, { passive: true });
    dialog.addEventListener("touchend", function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) show(index + (dx < 0 ? 1 : -1));
      startX = null;
    });
  }

  /* Steam widget: create the iframe only when it nears the viewport (Steam's page pulls ~400 KB). */
  Array.prototype.forEach.call(doc.querySelectorAll("[data-widget-src]"), function (shell) {
    var load = function () {
      if (shell.querySelector("iframe")) return;
      var frame = doc.createElement("iframe");
      frame.src = shell.getAttribute("data-widget-src");
      frame.title = shell.getAttribute("data-widget-title");
      frame.width = "646";
      frame.height = "190";
      frame.addEventListener("load", function () {
        shell.classList.add("is-loaded");
      });
      shell.appendChild(frame);
    };
    if (!("IntersectionObserver" in window)) return load();
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) {
        io.disconnect();
        load();
      }
    }, { rootMargin: "300px 0px" });
    io.observe(shell);
  });

  /* Language menu: close on outside click and on Escape. */
  Array.prototype.forEach.call(doc.querySelectorAll("[data-lang-menu]"), function (menu) {
    doc.addEventListener("click", function (e) {
      if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
    menu.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.open) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    });
  });
})();
