(function () {
  var SUPPORTS_LOCAL_STORAGE = supportsLocalStorage();
  var STORAGE_PREFIX = "mycontabile:";

  var timings = [];

  var articles = document.getElementsByTagName("article");
  for (var i = 0, ilen = articles.length; i < ilen; i += 1) {
    var article = articles[i];
    timings.push(makeTiming(article));
    addBkmkBttn(article);
  }

  updateNow(true);

  function makeTiming(article) {
    var timing = { elem: article };
    var times = article.getElementsByTagName("time");
    for (var o = 0, olen = times.length; o < olen; o += 1) {
      var time = times[o];
      timing[time.className] = Date.parse(time.getAttribute("dateTime"));
    }
    return timing;
  }

  function updateNow(scrollToNow) {
    var now = new Date();
    for (var i = 0, ilen = timings.length; i < ilen; i += 1) {
      var timing = timings[i];
      if (timing.start < now && timing.end > now) {
        timing.elem.classList.add("now");

        if (scrollToNow) {
          timing.elem.scrollIntoView(true);

          // Only scroll to the first now
          scrollToNow = false;
        }
      } else {
        timing.elem.classList.remove("now");
      }
    }

    setTimeout(updateNow, 60000);
  }

  function addBkmkBttn(article) {
    var eventName = article.id;

    // <a class="bookmark" href="#"></a>
    var bttn = document.createElement("a");
    bttn.className = "bkmk";
    bttn.href = "#";
    bttn.ariaLabel = "Bookmark this event";
    bttn.addEventListener("click", toggleBkmk, false);

    if (isBkmkedInStorage(eventName)) {
      bttn.classList.add("selected");
    }

    article.appendChild(bttn);
  }

  function toggleBkmk(e) {
    var bttn = e.target;
    var eventName = bttn.parentNode.id;

    bttn.classList.toggle("selected");
    toggleBkmkStorage(eventName);

    e.preventDefault();
    return false;
  }

  function toggleBkmkStorage(eventName) {
    if (!isBkmkedInStorage(eventName)) {
      addBkmkToStorage(eventName);
    } else {
      removeBkmkFromStorage(eventName);
    }
  }

  function storageKey(eventName) {
    return STORAGE_PREFIX + eventName;
  }

  function isBkmkedInStorage(eventName) {
    var key = storageKey(eventName);
    if (SUPPORTS_LOCAL_STORAGE) {
      return !!localStorage.getItem(key);
    } else {
      return new RegExp("(^|;\\s*)" + key + "=true").test(document.cookie);
    }
  }

  function addBkmkToStorage(eventName) {
    var key = storageKey(eventName);
    if (SUPPORTS_LOCAL_STORAGE) {
      localStorage.setItem(key, true);
    } else {
      document.cookie = key + "=true; expires=Fri, 31 Dec 9999 23:59:59 GMT";
    }
  }

  function removeBkmkFromStorage(eventName) {
    var key = storageKey(eventName);
    if (SUPPORTS_LOCAL_STORAGE) {
      localStorage.removeItem(key);
    } else {
      document.cookie = key + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
  }

  function supportsLocalStorage() {
    try {
      return "localStorage" in window && window["localStorage"] !== null;
    } catch (e) {
      return false;
    }
  }
})();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js");
}
