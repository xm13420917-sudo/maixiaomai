const PHONE = "18125834755";
const WHATSAPP = "8618125834755";
const PRODUCT_MAP = {
  shell_jz_1: "汫洲原产地带壳大蚝（A+）",
  shell_jz_2: "潮州鲜活带壳生蚝（标准）",
  half_shell_1: "烧烤店专供半壳生蚝",
  half_shell_2: "酒店摆盘半壳生蚝",
  meat_1: "生蚝肉（净肉）",
  meat_2: "速冻生蚝肉（餐饮装）",
  mini_1: "精品小蚝（蒜蓉/炭烤适配）",
  mini_2: "小规格鲜蚝（电商团购装）"
};

function getQuoteItems() {
  try {
    return JSON.parse(localStorage.getItem("oysterQuoteItems") || "[]");
  } catch {
    return [];
  }
}

function setQuoteItems(items) {
  localStorage.setItem("oysterQuoteItems", JSON.stringify(items));
  renderQuoteCount();
}

function addQuoteItem(itemId) {
  const items = getQuoteItems();
  if (!items.includes(itemId)) {
    items.push(itemId);
    setQuoteItems(items);
  }
}

function removeQuoteItem(itemId) {
  const items = getQuoteItems().filter((id) => id !== itemId);
  setQuoteItems(items);
}

function clearQuote() {
  localStorage.removeItem("oysterQuoteItems");
  renderQuoteCount();
  renderQuoteList();
}

function renderQuoteCount() {
  const count = getQuoteItems().length;
  document.querySelectorAll("[data-quote-count]").forEach((el) => {
    el.textContent = count;
  });
}

function renderQuoteList() {
  const holder = document.querySelector("#quote-list");
  if (!holder) {
    return;
  }
  const items = getQuoteItems();
  if (!items.length) {
    holder.innerHTML = "<p style=\"margin:0;color:#5f7285\">当前询价单为空，可在产品页点“加入询价单”。</p>";
    return;
  }
  const lines = items
    .map((id) => {
      const name = PRODUCT_MAP[id] || id;
      return `<li>${name} <button type=\"button\" class=\"pill\" data-remove=\"${id}\">移除</button></li>`;
    })
    .join("");
  holder.innerHTML = `<ul>${lines}</ul><button type=\"button\" id=\"clear-quote\" class=\"pill\" style=\"margin-top:8px\">清空询价单</button>`;

  holder.querySelectorAll("[data-remove]").forEach((btn) => {
    btn.addEventListener("click", () => {
      removeQuoteItem(btn.getAttribute("data-remove"));
      renderQuoteList();
    });
  });

  const clearBtn = holder.querySelector("#clear-quote");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => clearQuote());
  }
}

function buildInquiryMessage(form) {
  const fd = new FormData(form);
  const quoteItems = getQuoteItems().map((id) => PRODUCT_MAP[id] || id);
  const lines = [
    "【潮州生蚝批发询价】",
    `联系人：${fd.get("name") || ""}`,
    `手机：${fd.get("phone") || ""}`,
    `采购类型：${fd.get("biz_type") || ""}`,
    `城市/档口：${fd.get("city") || ""}`,
    `需求品类：${fd.get("category") || ""}`,
    `预计数量：${fd.get("quantity") || ""}`,
    `到货时间：${fd.get("delivery_date") || ""}`,
    `备注：${fd.get("remark") || "无"}`,
    `询价单：${quoteItems.length ? quoteItems.join("、") : "未勾选产品"}`,
    "产地偏好：广东潮州饶平汫洲"
  ];
  return lines.join("\n");
}

function bindAddQuoteButtons() {
  document.querySelectorAll("[data-add-quote]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-add-quote");
      addQuoteItem(id);
      btn.textContent = "已加入询价单";
      btn.disabled = true;
    });
  });
}

function bindInquiryForm() {
  const form = document.querySelector("#inquiry-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = buildInquiryMessage(form);
    const encoded = encodeURIComponent(message);
    const waUrl = `https://wa.me/${WHATSAPP}?text=${encoded}`;
    const preview = document.querySelector("#submit-preview");
    if (preview) {
      preview.textContent = "询价信息已生成，正在打开 WhatsApp；如未安装 WhatsApp，请直接电话/微信联系。";
    }
    window.open(waUrl, "_blank");
  });

  const copyBtn = document.querySelector("#copy-inquiry");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const msg = buildInquiryMessage(form);
      try {
        await navigator.clipboard.writeText(msg);
        copyBtn.textContent = "已复制询价内容";
      } catch {
        copyBtn.textContent = "复制失败，请手动复制";
      }
    });
  }

  const callBtn = document.querySelector("#call-now");
  if (callBtn) {
    callBtn.addEventListener("click", () => {
      window.location.href = `tel:${PHONE}`;
    });
  }
}

function setYear() {
  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = String(new Date().getFullYear());
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderQuoteCount();
  renderQuoteList();
  bindAddQuoteButtons();
  bindInquiryForm();
  setYear();
});
