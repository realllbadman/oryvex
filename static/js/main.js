/* ============================================================================
   Research Peptides — storefront client logic
   - 21+ age gate (sessionStorage)
   - cart (localStorage "pep_cart") + drawer with shipping math
   - quote/inquiry modal → POST /api/bookings/
   - COA viewer modal (image or embedded PDF)
   - live product filter + category-from-URL
   - delegated add-to-cart + variant selection (product detail)
   Public API exposed as window.PeptStore.
   ========================================================================== */
(function () {
  "use strict";

  var CART_KEY = "pep_cart";
  var AGE_KEY = "pep_age_ok";
  var COUPON_KEY = "pep_coupon";
  var body = document.body;
  var FREE_SHIP = parseFloat(body.getAttribute("data-free-ship") || "200");
  var FLAT_SHIP = parseFloat(body.getAttribute("data-flat-ship") || "15");
  var PHONE = body.getAttribute("data-business-phone") || "";

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var money = function (n) { return "$" + Number(n).toFixed(2); };

  // ─── Cart storage ──────────────────────────────────────────────
  function getCart() {
    try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
    catch (e) { return []; }
  }
  function setCart(c) { localStorage.setItem(CART_KEY, JSON.stringify(c)); renderCart(); }

  function addToCart(item) {
    if (!item || !item.slug) return;
    var cart = getCart();
    var key = item.slug + "|" + (item.strength || "");
    var found = cart.filter(function (c) { return (c.slug + "|" + (c.strength || "")) === key; })[0];
    if (found) { found.qty += (item.qty || 1); }
    else {
      cart.push({
        slug: item.slug, name: item.name, strength: item.strength || "",
        price: Number(item.price) || 0, qty: item.qty || 1, image: item.image || ""
      });
    }
    setCart(cart);
    toast(item.name + (item.strength ? " (" + item.strength + ")" : "") + " added to cart");
    openCart();
  }

  function changeQty(slug, strength, delta) {
    var cart = getCart();
    var key = slug + "|" + (strength || "");
    cart = cart.map(function (c) {
      if ((c.slug + "|" + (c.strength || "")) === key) c.qty += delta;
      return c;
    }).filter(function (c) { return c.qty > 0; });
    setCart(cart);
  }
  function removeItem(slug, strength) {
    var key = slug + "|" + (strength || "");
    setCart(getCart().filter(function (c) { return (c.slug + "|" + (c.strength || "")) !== key; }));
  }

  function cartCount() { return getCart().reduce(function (n, c) { return n + c.qty; }, 0); }
  function cartSubtotal() { return getCart().reduce(function (s, c) { return s + c.price * c.qty; }, 0); }
  function cartShipping(sub) { return sub >= FREE_SHIP ? 0 : (sub > 0 ? FLAT_SHIP : 0); }

  function renderCart() {
    var badge = $("#cartBadge");
    if (badge) badge.textContent = cartCount();
    var box = $("#cartItems");
    if (!box) return;
    var cart = getCart();
    if (!cart.length) {
      box.innerHTML = '<div class="cart-empty">Your cart is empty.<br/>Browse the catalog to add research compounds.</div>';
    } else {
      box.innerHTML = cart.map(function (c) {
        return '' +
          '<div class="cart-item">' +
            '<img class="ci-img" src="' + (c.image || "/static/images/placeholder.jpg") + '" alt="" />' +
            '<div style="flex:1;">' +
              '<div class="ci-name">' + c.name + '</div>' +
              '<div class="ci-meta">' + (c.strength || "—") + " · " + money(c.price) + '</div>' +
              '<div style="margin-top:6px;display:flex;justify-content:space-between;align-items:center;">' +
                '<span class="qty">' +
                  '<button data-q="-" data-slug="' + c.slug + '" data-str="' + c.strength + '">−</button>' +
                  '<span>' + c.qty + '</span>' +
                  '<button data-q="+" data-slug="' + c.slug + '" data-str="' + c.strength + '">+</button>' +
                '</span>' +
                '<button class="ci-remove" data-remove data-slug="' + c.slug + '" data-str="' + c.strength + '">Remove</button>' +
              '</div>' +
            '</div>' +
          '</div>';
      }).join("");
    }
    var sub = cartSubtotal();
    var ship = cartShipping(sub);
    if ($("#cartSubtotal")) $("#cartSubtotal").textContent = money(sub);
    if ($("#cartShipping")) $("#cartShipping").textContent = sub === 0 ? "—" : (ship === 0 ? "FREE" : money(ship));
    if ($("#cartTotal")) $("#cartTotal").textContent = money(sub + ship);
  }

  // ─── Drawer + overlay ──────────────────────────────────────────
  function openCart() { $("#cartDrawer").classList.add("show"); $("#overlay").classList.add("show"); }
  function closeAll() {
    $("#cartDrawer").classList.remove("show");
    $("#overlay").classList.remove("show");
    $$(".modal").forEach(function (m) { m.classList.remove("show"); });
  }
  function closeMobileMenu() {
    var mm = $("#mobileMenu");
    if (mm) mm.classList.remove("show");
  }

  // ─── Toast ─────────────────────────────────────────────────────
  var toastTimer;
  function toast(msg) {
    var t = $("#toast");
    if (!t) return;
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("show"); }, 2600);
  }

  // ─── Quote / inquiry modal ─────────────────────────────────────
  function openQuote(topic, product) {
    var m = $("#quoteModal");
    if (!m) return;
    if (topic) { var s = $('#quoteForm [name="service"]'); if (s) s.value = topic; }
    if (product) { var p = $('#quoteForm [name="product_interest"]'); if (p) p.value = product; }
    m.classList.add("show");
  }

  function submitQuote(e) {
    e.preventDefault();
    var form = e.target;
    var data = {};
    $$("input, select, textarea", form).forEach(function (el) {
      if (el.name) data[el.name] = el.value;
    });
    var btn = $("button[type=submit]", form);
    if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
    fetch("/api/bookings/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(function (r) {
      if (!r.ok) throw new Error("bad status");
      form.reset(); closeAll();
      toast("Thanks — we'll be in touch shortly.");
    }).catch(function () {
      toast("Couldn't send." + (PHONE ? " Call " + PHONE : ""));
    }).finally(function () {
      if (btn) { btn.disabled = false; btn.textContent = "Send Inquiry"; }
    });
  }

  // ─── COA viewer ────────────────────────────────────────────────
  function openCOA(slug, name, coaFile, coaLab) {
    var m = $("#coaModal");
    if (!m) return;
    $("#coaTitle").textContent = "COA — " + name;
    var v = $("#coaViewer");
    if (coaFile) {
      var isPdf = /\.pdf($|\?)/i.test(coaFile);
      var labLine = coaLab ? '<p class="muted" style="margin:0 0 12px;">Tested by: ' + coaLab + "</p>" : "";
      v.innerHTML = labLine + (isPdf
        ? '<iframe src="' + coaFile + '" title="COA PDF"></iframe>'
        : '<img src="' + coaFile + '" alt="Certificate of Analysis" />');
    } else {
      v.innerHTML = '<div class="center" style="padding:40px 0;">' +
        '<div style="font-size:34px;">📄</div>' +
        '<h3 style="margin:10px 0 6px;">COA pending</h3>' +
        '<p class="muted">A Certificate of Analysis has not been uploaded for this product yet. ' +
        'Request one and we\'ll send it over.</p>' +
        '<button class="btn btn-primary btn-sm" onclick="PeptStore.openQuote(\'Request COA\',\'' + name.replace(/'/g, "") + '\')">Request COA</button>' +
        "</div>";
    }
    m.classList.add("show");
  }

  // ─── Scroll-reveal statement (word-by-word fill) ───────────────
  function initReveal() {
    var section = $(".reveal-section");
    if (!section) return;
    var words = $$(".rv-word", section);
    var ticking = false;
    function update() {
      ticking = false;
      var rect = section.getBoundingClientRect();
      var total = section.offsetHeight - window.innerHeight;
      var progress = total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 0;
      // ease so words fill across the middle of the scroll, not the very ends
      var active = Math.round(Math.min(1, progress * 1.25) * words.length);
      for (var i = 0; i < words.length; i++) words[i].classList.toggle("on", i < active);
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  // ─── Holiday promo bar (auto-targets the next major US holiday) ──
  function nthWeekday(year, month, weekday, n) {   // month 0-11, weekday 0=Sun
    var first = new Date(year, month, 1);
    var offset = (weekday - first.getDay() + 7) % 7;
    return new Date(year, month, 1 + offset + (n - 1) * 7);
  }
  function lastWeekday(year, month, weekday) {
    var last = new Date(year, month + 1, 0);       // last day of month
    var offset = (last.getDay() - weekday + 7) % 7;
    return new Date(year, month, last.getDate() - offset);
  }
  function usHolidays(year) {
    var thanks = nthWeekday(year, 10, 4, 4);        // 4th Thursday of Nov
    return [
      { name: "New Year's",       date: new Date(year, 0, 1) },
      { name: "MLK Day",          date: nthWeekday(year, 0, 1, 3) },
      { name: "Valentine's Day",  date: new Date(year, 1, 14) },
      { name: "Presidents' Day",  date: nthWeekday(year, 1, 1, 3) },
      { name: "Memorial Day",     date: lastWeekday(year, 4, 1) },
      { name: "Juneteenth",       date: new Date(year, 5, 19) },
      { name: "Independence Day", date: new Date(year, 6, 4) },
      { name: "Labor Day",        date: nthWeekday(year, 8, 1, 1) },
      { name: "Halloween",        date: new Date(year, 9, 31) },
      { name: "Veterans Day",     date: new Date(year, 10, 11) },
      { name: "Thanksgiving",     date: thanks },
      { name: "Black Friday",     date: new Date(year, 10, thanks.getDate() + 1) },
      { name: "Cyber Monday",     date: new Date(year, 10, thanks.getDate() + 4) },
      { name: "Christmas",        date: new Date(year, 11, 25) },
      { name: "New Year's Eve",   date: new Date(year, 11, 31) }
    ];
  }
  function nextHoliday() {
    var now = new Date();
    var list = usHolidays(now.getFullYear()).concat(usHolidays(now.getFullYear() + 1));
    for (var i = 0; i < list.length; i++) {
      var d = list[i].date;
      var end = new Date(d.getFullYear(), d.getMonth(), d.getDate(), 23, 59, 59).getTime();
      if (end >= now.getTime()) return { name: list[i].name, end: end };
    }
    return null;
  }
  function initPromoCountdown() {
    var el = $("#promoCountdown");
    var textEl = $(".promo-text");
    if (!el) return;
    function tick() {
      var h = nextHoliday();
      if (!h) return;
      if (textEl) textEl.textContent = h.name + " Sale";
      var remaining = Math.max(0, h.end - Date.now());
      var s = Math.floor(remaining / 1000);
      var d = Math.floor(s / 86400); s -= d * 86400;
      var hh = Math.floor(s / 3600); s -= hh * 3600;
      var m = Math.floor(s / 60); s -= m * 60;
      var pad = function (n) { return (n < 10 ? "0" : "") + n; };
      el.textContent = d + "d " + pad(hh) + "h " + pad(m) + "m " + pad(s) + "s";
    }
    tick();
    setInterval(tick, 1000);
  }

  // ─── Coupons + announcement bar ────────────────────────────────
  function getCoupon() { return (localStorage.getItem(COUPON_KEY) || "").toUpperCase(); }
  function setCoupon(code) {
    if (!code) return;
    localStorage.setItem(COUPON_KEY, code.toUpperCase());
    renderAnnounce();
  }
  function clearCoupon() { localStorage.removeItem(COUPON_KEY); renderAnnounce(); }

  function renderAnnounce() {
    var bar = $("#announceBar");
    if (!bar) return;
    var code = getCoupon();
    if (code) {
      $("#announceText").innerHTML = "🎉 Code <strong>" + code + "</strong> applied — it'll be used at checkout.";
      bar.hidden = false;
    } else {
      bar.hidden = true;
    }
  }

  // capture ?coupon=CODE from the URL, store it, and clean the URL
  function captureCouponFromUrl() {
    var params = new URLSearchParams(location.search);
    var code = params.get("coupon");
    if (code) {
      setCoupon(code);
      toast("Coupon " + code.toUpperCase() + " saved");
      params.delete("coupon");
      var q = params.toString();
      history.replaceState({}, "", location.pathname + (q ? "?" + q : ""));
    }
    renderAnnounce();
  }

  // ─── Newsletter / Get 15% Off ──────────────────────────────────
  var NL_CODE = "RESEARCH20"; // owner: keep in sync with an active coupon
  function openNewsletter() {
    var m = $("#newsletterModal");
    if (!m) return;
    $("#newsletterForm").style.display = "block";
    $("#newsletterDone").style.display = "none";
    m.classList.add("show");
  }
  function submitNewsletter(e) {
    e.preventDefault();
    var form = e.target, data = { service: "Newsletter Signup", details: "Requested discount code (15% off promo)" };
    $$("input", form).forEach(function (el) { if (el.name) data[el.name] = el.value; });
    if (!data.last_name) data.last_name = "-";
    var btn = $("button[type=submit]", form);
    if (btn) { btn.disabled = true; btn.textContent = "…"; }
    fetch("/api/bookings/", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data)
    }).then(function (r) {
      if (!r.ok) throw new Error();
      setCoupon(NL_CODE);
      $("#nlCode").textContent = NL_CODE;
      try { navigator.clipboard && navigator.clipboard.writeText(NL_CODE); } catch (e2) {}
      $("#newsletterForm").style.display = "none";
      $("#newsletterDone").style.display = "block";
    }).catch(function () {
      toast("Couldn't sign up — please try again.");
    }).finally(function () { if (btn) { btn.disabled = false; btn.textContent = "Get My Code"; } });
  }

  // ─── Reconstitution calculator (research reference) ────────────
  function computeCalc() {
    var out = $("#calcOut");
    if (!out) return;
    var mg = parseFloat($("#calcMg").value) || 0;
    var ml = parseFloat($("#calcMl").value) || 0;
    var upl = parseFloat($("#calcSyringe").value) || 100; // units per mL
    if (mg <= 0 || ml <= 0) { out.innerHTML = '<p class="co-hint">Enter a peptide mass and solvent volume.</p>'; return; }
    var mgPerMl = mg / ml;
    var mcgPerMl = mgPerMl * 1000;
    var mcgPerUnit = mcgPerMl / upl;          // mcg per 1 syringe unit
    var mcgPer10Units = mcgPerUnit * 10;
    out.innerHTML =
      '<div class="co-line"><span>Concentration</span><b>' + mgPerMl.toFixed(2) + ' mg/mL</b></div>' +
      '<div class="co-line"><span>Concentration</span><b>' + Math.round(mcgPerMl) + ' mcg/mL</b></div>' +
      '<div class="co-line"><span>Per syringe unit</span><b>' + mcgPerUnit.toFixed(1) + ' mcg / unit</b></div>' +
      '<div class="co-line"><span>Per 10 units</span><b>' + mcgPer10Units.toFixed(0) + ' mcg</b></div>' +
      '<p class="co-hint">Based on a ' + upl + ' units/mL syringe. Reconstitution reference for laboratory research only — not dosing guidance.</p>';
  }

  // ─── Age gate ──────────────────────────────────────────────────
  function initAgeGate() {
    var gate = $("#ageGate");
    if (!gate) return;
    if (sessionStorage.getItem(AGE_KEY) === "1") { gate.remove(); return; }
    gate.hidden = false;
    body.classList.add("no-scroll");
    $("#ageAccept").addEventListener("click", function () {
      sessionStorage.setItem(AGE_KEY, "1");
      body.classList.remove("no-scroll");
      gate.remove();
    });
    $("#ageExit").addEventListener("click", function () {
      window.location.href = "https://www.google.com";
    });
  }

  // ─── Product filter (catalog) ──────────────────────────────────
  function initFilter() {
    var grid = $("#productGrid");
    if (!grid) return;
    var search = $("#searchInput");
    var select = $("#categorySelect");     // legacy dropdown (optional)
    var chips = $("#catFilter");            // chip-style filter (optional)
    var none = $("#noResults");
    var countEl = $("#catCount");

    // preselect category from ?category=
    var params = new URLSearchParams(location.search);
    var cat = params.get("category") || "";
    if (cat && select) select.value = cat;
    if (chips) {
      var matched = false;
      $$(".chip", chips).forEach(function (c) {
        var on = (c.getAttribute("data-cat") || "") === cat;
        c.classList.toggle("active", on); if (on) matched = true;
      });
      if (!matched) { var all = chips.querySelector('.chip[data-cat=""]'); if (all) all.classList.add("active"); }
    }

    function currentCat() {
      if (chips) { var a = chips.querySelector(".chip.active"); return a ? (a.getAttribute("data-cat") || "") : ""; }
      return (select && select.value) || "";
    }
    function syncUrl(v) {
      var url = new URL(location.href);
      if (v) url.searchParams.set("category", v); else url.searchParams.delete("category");
      history.replaceState({}, "", url);
    }
    function apply() {
      var q = (search && search.value || "").toLowerCase().trim();
      var c = currentCat();
      var visible = 0;
      $$(".pcard", grid).forEach(function (card) {
        var name = (card.getAttribute("data-name") || "").toLowerCase();
        var category = card.getAttribute("data-category") || "";
        var ok = (!q || name.indexOf(q) !== -1) && (!c || category === c);
        card.classList.toggle("hidden", !ok);
        if (ok) visible++;
      });
      if (none) none.classList.toggle("hidden", visible !== 0);
      if (countEl) countEl.textContent = visible;
    }
    if (search) search.addEventListener("input", apply);
    if (select) select.addEventListener("change", function () { apply(); syncUrl(select.value); });
    if (chips) chips.addEventListener("click", function (e) {
      var b = e.target.closest(".chip"); if (!b) return;
      $$(".chip", chips).forEach(function (c) { c.classList.remove("active"); });
      b.classList.add("active");
      if (search) search.value = "";   // picking a category shouldn't stay filtered by a stale search
      apply(); syncUrl(b.getAttribute("data-cat") || "");
    });
    apply();
  }

  // ─── Active category chip from URL ─────────────────────────────
  function initChips() {
    var params = new URLSearchParams(location.search);
    var cat = params.get("category") || "";
    $$("#catChips .chip").forEach(function (chip) {
      if ((chip.getAttribute("data-cat") || "") === cat) chip.classList.add("active");
    });
  }

  // ─── Global delegated events ───────────────────────────────────
  function initEvents() {
    document.addEventListener("click", function (e) {
      var t = e.target;

      // open cart
      if (t.closest("#cartBtn")) { openCart(); return; }
      // close buttons / overlay
      if (t.closest("[data-close]") || t.id === "overlay") { closeAll(); return; }
      // ask a question (nav button or mobile-menu link)
      if (t.closest("#askBtn") || t.closest(".js-ask")) {
        e.preventDefault(); closeMobileMenu(); openQuote("General Inquiry", ""); return;
      }
      // floating discount → newsletter (Get 15% Off)
      if (t.closest("#discountBtn")) { openNewsletter(); return; }
      // calculator (nav button or mobile-menu link)
      if (t.closest("#calcBtn") || t.closest(".js-calc")) {
        e.preventDefault(); closeMobileMenu(); $("#calcModal").classList.add("show"); computeCalc(); return;
      }
      // remove active coupon from the announcement bar
      if (t.closest("#announceClear")) { clearCoupon(); return; }
      // best-sellers carousel arrows
      if (t.closest("#bsPrev") || t.closest("#bsNext")) {
        var track = $("#bsTrack");
        if (track) track.scrollBy({ left: t.closest("#bsNext") ? 318 : -318, behavior: "smooth" });
        return;
      }
      // apply newsletter code → go shop
      if (t.closest("#nlApply")) { closeAll(); if (location.pathname !== "/products") location.href = "/products"; return; }
      // search button → go to catalog + focus
      if (t.closest("#searchBtn")) {
        if (location.pathname !== "/products") location.href = "/products";
        else { var s = $("#searchInput"); if (s) s.focus(); }
        return;
      }
      // mobile menu
      if (t.closest("#navToggle")) { $("#mobileMenu").classList.toggle("show"); return; }

      // cart qty +/-
      var q = t.closest("[data-q]");
      if (q) { changeQty(q.getAttribute("data-slug"), q.getAttribute("data-str"), q.getAttribute("data-q") === "+" ? 1 : -1); return; }
      var rm = t.closest("[data-remove]");
      if (rm) { removeItem(rm.getAttribute("data-slug"), rm.getAttribute("data-str")); return; }

      // FAQ accordion
      var fq = t.closest(".faq-q");
      if (fq) { fq.parentElement.classList.toggle("open"); return; }

      // delegated add-to-cart (require a size when the product has a selector)
      var reveal = t.closest("[data-reveal]");
      if (reveal) {
        var target = document.getElementById(reveal.getAttribute("data-reveal"));
        if (target) { target.classList.remove("hidden"); reveal.style.display = "none"; }
        return;
      }

      var add = t.closest("[data-add-to-cart]");
      if (add) {
        if (document.getElementById("pdSwatches") && !add.getAttribute("data-strength")) {
          toast("Please choose a strength.");
          return;
        }
        var qtyEl = document.getElementById("pdQty");
        addToCart({
          slug: add.getAttribute("data-slug"),
          name: add.getAttribute("data-name"),
          strength: add.getAttribute("data-strength"),
          price: add.getAttribute("data-price"),
          qty: qtyEl ? Math.max(1, parseInt(qtyEl.value, 10) || 1) : 1,
          image: add.getAttribute("data-image")
        });
        return;
      }
    });

    var qf = $("#quoteForm");
    if (qf) qf.addEventListener("submit", submitQuote);

    var nl = $("#nlForm");
    if (nl) nl.addEventListener("submit", submitNewsletter);

    // footer subscribe box — email only, posts as a newsletter inquiry
    var nlF = $("#nlFooter");
    if (nlF) nlF.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = $("input[name=email]", nlF);
      var email = input && input.value.trim();
      if (!email) return;
      var btn = $("button[type=submit]", nlF);
      if (btn) btn.disabled = true;
      fetch("/api/bookings/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: "Newsletter", last_name: "-", email: email,
          service: "Newsletter Signup", details: "Subscribed from the footer form."
        })
      }).then(function (r) {
        if (!r.ok) throw new Error();
        nlF.reset();
        toast("Thanks — you're on the list.");
      }).catch(function () {
        toast("Couldn't subscribe — please try again.");
      }).finally(function () { if (btn) btn.disabled = false; });
    });

    ["calcMg", "calcMl", "calcSyringe"].forEach(function (id) {
      var el = $("#" + id);
      if (el) el.addEventListener("input", computeCalc);
      if (el) el.addEventListener("change", computeCalc);
    });

    // ESC closes overlays
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeAll(); });
  }

  // ─── Product-detail strength swatches + quantity ───────────────
  function applySwatch(btn) {
    var wrap = document.getElementById("pdSwatches");
    if (!wrap) return;
    var cleared = !btn;
    $$(".swatch", wrap).forEach(function (b) { b.classList.toggle("active", b === btn); });

    var addBtn = $("#addToCartBtn");
    var price = cleared ? "" : btn.getAttribute("data-price");
    var strength = cleared ? "" : btn.getAttribute("data-strength");
    if (addBtn) {
      addBtn.setAttribute("data-price", price || addBtn.getAttribute("data-base-price") || "");
      addBtn.setAttribute("data-strength", strength);
    }
    var disp = $("#pdPrice");
    if (disp && price) disp.textContent = Number(price).toFixed(2);
    var lbl = $("#pdStrengthLabel");
    if (lbl) lbl.textContent = strength || "Choose an option";
  }

  function initProductDetail() {
    var wrap = document.getElementById("pdSwatches");
    if (wrap) {
      wrap.addEventListener("click", function (e) {
        var b = e.target.closest(".swatch");
        if (b) applySwatch(b);
      });
      var clear = $("#pdClear");
      if (clear) clear.addEventListener("click", function () { applySwatch(null); });
    }
    var qty = $("#pdQty");
    if (qty) {
      var step = function (d) {
        var n = Math.max(1, (parseInt(qty.value, 10) || 1) + d);
        qty.value = n;
        var addBtn = $("#addToCartBtn");
        if (addBtn) addBtn.setAttribute("data-qty", n);
      };
      $("#qtyMinus").addEventListener("click", function () { step(-1); });
      $("#qtyPlus").addEventListener("click", function () { step(1); });
    }
  }

  // ─── Scroll reveals ────────────────────────────────────────────
  function initReveals() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    // tag the things worth animating, in document order
    var targets = $$([
      ".tested-stack .tb-block", ".sec-title", ".section > .wrap > .grid > .pcard",
      ".trio .tr", ".tested-cards .tc", ".about-grid > *", ".faq-item",
      ".closing > *", ".catalog-search", ".footer-grid.four > *"
    ].join(","));

    targets.forEach(function (el, i) {
      if (el.hasAttribute("data-anim")) return;
      var kind = el.closest(".about-grid") ? (el.matches(".about-photo") ? "right" : "left")
               : el.matches(".pcard") ? "zoom" : "up";
      el.setAttribute("data-anim", kind);
      el.style.transitionDelay = ((i % 4) * 70) + "ms";
    });

    if (!("IntersectionObserver" in window)) {
      targets.forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    targets.forEach(function (el) { io.observe(el); });
  }

  // ─── Boot ──────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", function () {
    initAgeGate();
    renderCart();
    initEvents();
    initFilter();
    initChips();
    initProductDetail();
    initReveals();
    captureCouponFromUrl();
    initPromoCountdown();
    initReveal();
  });

  // Public API for inline handlers in templates.
  window.PeptStore = {
    addToCart: addToCart,
    openQuote: openQuote,
    openCOA: openCOA,
    openCart: openCart,
    openNewsletter: openNewsletter,
    getCoupon: getCoupon,
    setCoupon: setCoupon,
    clearCoupon: clearCoupon,
    toast: toast
  };
})();
