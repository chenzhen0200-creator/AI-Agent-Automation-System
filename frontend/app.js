"use strict";

const $ = (id) => document.getElementById(id);
const conversation = $("conversation");
const clientId = localStorage.getItem("adlearn_client_id") || crypto.randomUUID();
localStorage.setItem("adlearn_client_id", clientId);
let conversationId = localStorage.getItem("adlearn_conversation_id");
const drawer = $("history-drawer");
function setHistoryOpen(open) {
  drawer.classList.toggle("open", open);
  drawer.inert = !open;
  drawer.setAttribute("aria-hidden", String(!open));
  $("history-backdrop").hidden = !open;
  $("history-toggle").setAttribute("aria-expanded", String(open));
  if (open) $("history-close").focus();
  else $("history-toggle").focus();
}
$("history-toggle").addEventListener("click", () => setHistoryOpen(!drawer.classList.contains("open")));
$("history-close").addEventListener("click", () => setHistoryOpen(false));
$("history-backdrop").addEventListener("click", () => setHistoryOpen(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (!$("image-lightbox").hidden) closeLightbox();
    else if (drawer.classList.contains("open")) setHistoryOpen(false);
  }
});

function clearConversation() {
  conversation.replaceChildren();
  const empty = node("div", "empty-chat");
  empty.append(node("strong", "", "从一个问题开始"), node("span", "", "例如：Google Ads CTR 是什么？"));
  conversation.append(empty);
}

async function loadHistory() {
  try {
    const data = await requestJson(`/conversations?client_id=${encodeURIComponent(clientId)}`);
    const list = $("history-list");
    list.replaceChildren();
    data.conversations.forEach((item) => {
      const row = node("div", `history-item${item.id === conversationId ? " active" : ""}`);
      const open = node("button", "history-open", item.title);
      open.type = "button";
      open.addEventListener("click", () => openConversation(item.id));
      const menu = node("details", "history-menu");
      menu.append(node("summary", "", "⋯"));
      menu.querySelector("summary").setAttribute("aria-label", `${item.title} 的更多操作`);
      const remove = node("button", "history-delete", "Delete");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!confirm("确定删除这个对话吗？")) return;
        try {
          await requestJson(`/conversations/${item.id}?client_id=${encodeURIComponent(clientId)}`, { method: "DELETE" });
          if (conversationId === item.id) newChat();
          await loadHistory();
        } catch (error) { $("history-status").textContent = error.message; }
      });
      menu.append(remove);
      row.append(open, menu);
      list.append(row);
    });
    $("history-status").textContent = data.conversations.length ? `${data.conversations.length} 个对话` : "暂无历史对话";
  } catch (error) {
    $("history-status").textContent = error.message.includes("Database Not Configured") ? "Database Not Configured" : `历史记录不可用：${error.message}`;
  }
}

async function openConversation(id) {
  try {
    const data = await requestJson(`/conversations/${id}/messages?client_id=${encodeURIComponent(clientId)}`);
    conversationId = id;
    localStorage.setItem("adlearn_conversation_id", id);
    clearConversation();
    data.messages.forEach((item) => {
      const meta = item.metadata;
      const restored = meta?.intent === "steps" && Array.isArray(meta.steps)
        ? { intent: "steps", platform: meta.platform, execution_mode: item.execution_mode,
            tool_results: [{ tool_name: meta.tool_name, success: true, result: { topic: meta.topic, steps: meta.steps } }] }
        : null;
      showChatMessage(item.role === "user" ? "user" : "agent", item.content, restored);
    });
    setHistoryOpen(false);
    await loadHistory();
  } catch (error) { $("history-status").textContent = error.message; }
}

function newChat() {
  conversationId = null;
  localStorage.removeItem("adlearn_conversation_id");
  clearConversation();
  $("message").focus();
}

$("new-chat").addEventListener("click", () => { newChat(); setHistoryOpen(false); loadHistory(); });

function node(tag, className = "", text = "") {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== "") item.textContent = String(text);
  return item;
}

function validLink(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.href : null;
  } catch { return null; }
}

function friendlyError(data, status) {
  if (data?.detail === "Database Not Configured") return "Database Not Configured";
  if (status === 429) return "请求较多，请稍后再试。";
  if (status === 422) return "输入格式不正确，请检查内容后重试。";
  if (status >= 500) return "服务暂时无法处理请求，请稍后再试。";
  if (data?.error_type === "Search API Not Configured")
    return "当前尚未配置外部搜索服务，因此最新官方资料自动检索暂不可用。";
  return data?.message || data?.answer || "请求未完成，请稍后重试。";
}

async function requestJson(path, options = {}) {
  const controller = new AbortController();
  const wakeTimer = setTimeout(() => {
    const status = options.statusElement;
    if (status) status.textContent = "AdLearn 服务正在启动，请稍候…";
  }, 3500);
  const timeout = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(path, { ...options, signal: controller.signal });
    let data;
    try { data = await response.json(); }
    catch { throw new Error("服务返回了无法读取的响应，请稍后再试。"); }
    if (!response.ok) throw new Error(friendlyError(data, response.status));
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("AdLearn 服务启动较慢，请稍后重试。");
    if (error instanceof TypeError) throw new Error("网络连接失败，请检查网络后重试。");
    throw error;
  } finally {
    clearTimeout(wakeTimer);
    clearTimeout(timeout);
  }
}

function detailRow(container, label, value) {
  if (value === undefined || value === null || value === "") return;
  const row = node("div", "details-row");
  row.append(node("strong", "", `${label}: `), document.createTextNode(String(value)));
  container.append(row);
}

function tutorialImageUrl(step) {
  const path = step?.image_url;
  const source = step?.image_source;
  if (step?.image_type !== "real_screenshot" ||
      !["user_upload", "google_official", "meta_official", "public_tutorial"].includes(source) ||
      typeof path !== "string" ||
      !/^\/static\/tutorial-images\/(google|meta)\/real\/(?:[a-z0-9-]+\/)+[a-z0-9-]+\.(png|jpg|jpeg|webp)$/.test(path)) return null;
  if (source !== "user_upload" && !validLink(step.source_url)) return null;
  return path;
}

const screenshotSources = {
  user_upload: "用户提供后台截图", google_official: "Google Ads 官方",
  meta_official: "Meta 官方", public_tutorial: "公开教程",
};

function screenshotOverlay(rawAnnotations) {
  if (!Array.isArray(rawAnnotations) || !rawAnnotations.length) return null;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "screenshot-annotations");
  svg.setAttribute("viewBox", "0 0 100 100");
  svg.setAttribute("preserveAspectRatio", "none");
  svg.setAttribute("aria-hidden", "true");
  const markerId = `adlearn-arrow-${crypto.randomUUID()}`;
  const defs = document.createElementNS(svg.namespaceURI, "defs");
  const marker = document.createElementNS(svg.namespaceURI, "marker");
  [["id", markerId], ["markerWidth", "5"], ["markerHeight", "5"], ["refX", "4"], ["refY", "2.5"],
   ["orient", "auto"], ["markerUnits", "strokeWidth"]].forEach(([key, value]) => marker.setAttribute(key, value));
  const tip = document.createElementNS(svg.namespaceURI, "path");
  tip.setAttribute("d", "M 0 0 L 5 2.5 L 0 5 z");
  tip.setAttribute("fill", "#e52e36");
  marker.append(tip);
  defs.append(marker);
  svg.append(defs);
  let count = 0;
  rawAnnotations.slice(0, 8).forEach((item) => {
    if (!item || !["box", "arrow"].includes(item.type)) return;
    const keys = item.type === "box" ? ["x", "y", "width", "height"] : ["x", "y", "to_x", "to_y"];
    if (keys.some((key) => typeof item[key] !== "number" || !Number.isFinite(item[key]) || item[key] < 0 || item[key] > 100)) return;
    if (item.type === "box" && (item.width <= 0 || item.height <= 0 || item.x + item.width > 100 || item.y + item.height > 100)) return;
    const shape = document.createElementNS(svg.namespaceURI, item.type === "box" ? "rect" : "line");
    const attributes = item.type === "box"
      ? { x: item.x, y: item.y, width: item.width, height: item.height, fill: "none", stroke: "#e52e36", "stroke-width": 0.85 }
      : { x1: item.x, y1: item.y, x2: item.to_x, y2: item.to_y, stroke: "#e52e36", "stroke-width": 0.9,
          "marker-end": `url(#${markerId})` };
    Object.entries(attributes).forEach(([key, value]) => shape.setAttribute(key, String(value)));
    svg.append(shape);
    count += 1;
  });
  return count ? svg : null;
}

function openLightbox(src, alt, annotations = []) {
  $("lightbox-image").src = src;
  $("lightbox-image").alt = alt;
  const media = $("lightbox-media");
  media.querySelector(".screenshot-annotations")?.remove();
  const overlay = screenshotOverlay(annotations);
  if (overlay) media.append(overlay);
  $("image-lightbox").hidden = false;
  $("lightbox-close").focus();
}

function closeLightbox() {
  $("image-lightbox").hidden = true;
  $("lightbox-image").removeAttribute("src");
  $("lightbox-media").querySelector(".screenshot-annotations")?.remove();
}
$("lightbox-close").addEventListener("click", closeLightbox);
$("image-lightbox").addEventListener("click", (event) => {
  if (event.target === $("image-lightbox")) closeLightbox();
});

function renderStepCard(step, platform, topic) {
  const card = node("article", "step-card");
  card.append(node("h3", "", `第 ${step.step_number} 步：${step.title || "操作"}`));
  const src = tutorialImageUrl(step);
  if (src) {
    const imageSection = node("div", "step-image-section");
    const button = node("button", "step-image-button");
    button.type = "button";
    const alt = `${platform === "meta_ads" ? "Meta Ads" : "Google Ads"} ${topic} 第 ${step.step_number} 步真实后台截图`;
    const img = node("img", "step-image");
    img.src = src;
    img.alt = alt;
    img.loading = "lazy";
    img.addEventListener("error", () => imageSection.replaceWith(node("p", "image-placeholder", "该步骤暂未收录真实后台截图")));
    button.append(img);
    const overlay = screenshotOverlay(step.annotations);
    if (overlay) button.append(overlay);
    button.addEventListener("click", () => openLightbox(src, alt, step.annotations));
    imageSection.append(button);
    const sourceLine = node("div", "image-source");
    sourceLine.append(node("span", "", `来源：${screenshotSources[step.image_source]}`));
    if (step.captured_at) sourceLine.append(node("span", "", `拍摄日期：${step.captured_at}`));
    const link = validLink(step.source_url);
    if (link) {
      const sourceDetails = node("details", "image-source-details");
      sourceDetails.append(node("summary", "", "查看来源"));
      const anchor = node("a", "", link);
      anchor.href = link;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      sourceDetails.append(anchor);
      sourceLine.append(sourceDetails);
    }
    imageSection.append(sourceLine);
    card.append(imageSection);
  } else card.append(node("p", "image-placeholder", "该步骤暂未收录真实后台截图"));
  card.append(node("p", "step-action", `操作：${step.action || "查看当前步骤。"}`));
  const details = node("details", "step-details");
  details.append(node("summary", "", "查看详细说明"));
  const body = node("div", "step-details-body");
  detailRow(body, "位置", step.ui_location);
  detailRow(body, "说明", step.description);
  detailRow(body, "预期结果", step.expected_result || step.next_page);
  detailRow(body, "界面位置提示", step.image_hint);
  details.append(body);
  card.append(details);
  return card;
}

function renderTutorial(data) {
  if (data?.intent !== "steps") return null;
  const tool = data.tool_results?.find((item) => item.success &&
    ["get_google_ads_steps", "get_meta_ads_steps"].includes(item.tool_name) && Array.isArray(item.result?.steps));
  if (!tool) return null;
  const result = tool.result;
  const section = node("section", "step-tutorial");
  section.append(node("h2", "", `${result.topic || "操作"} · 图文步骤`),
                 node("p", "tutorial-note", "AdLearn 操作教程 · 真实后台截图"));
  result.steps.slice(0, 8).forEach((step) => section.append(renderStepCard(step, data.platform, result.topic)));
  if (result.steps.length > 8) {
    const more = node("details", "more-steps");
    more.append(node("summary", "", `查看剩余 ${result.steps.length - 8} 步`));
    result.steps.slice(8).forEach((step) => more.append(renderStepCard(step, data.platform, result.topic)));
    section.append(more);
  }
  return section;
}

function showChatMessage(role, text, data = null, isError = false) {
  const empty = conversation.querySelector(".empty-chat");
  if (empty) empty.remove();
  const wrapper = node("div", `message ${role}`);
  wrapper.append(node("span", "message-label", role === "user" ? "You" : "Agent"));
  const tutorial = role === "agent" && !isError ? renderTutorial(data) : null;
  wrapper.append(tutorial || node("div", `bubble${isError ? " error" : ""}`, text));
  if (role === "agent" && data) {
    const details = node("details", "details");
    details.append(node("summary", "", "查看来源与执行详情"));
    const content = node("div", "details-content");
    const platforms = { google_ads: "Google Ads", meta_ads: "Meta Ads", cross_platform: "跨平台" };
    detailRow(content, "Platform", platforms[data.platform] || data.platform);
    detailRow(content, "Intent", data.intent);
    detailRow(content, "Execution Mode", data.execution_mode);
    if (Array.isArray(data.sources) && data.sources.length) {
      const sources = node("div", "details-row");
      sources.append(node("strong", "", "Sources: "));
      data.sources.forEach((source) => {
        const href = validLink(source.url);
        if (!href) return;
        const link = node("a", "source-link", source.title || href);
        link.href = href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        sources.append(link, document.createTextNode(" "));
      });
      content.append(sources);
    }
    if (Array.isArray(data.warnings)) data.warnings.forEach((warning) => detailRow(content, "Warning", warning.message || warning));
    if (Array.isArray(data.execution_trace)) detailRow(content, "Execution Trace", data.execution_trace.join(" → "));
    details.append(content);
    wrapper.append(details);
  }
  conversation.append(wrapper);
  conversation.scrollTop = conversation.scrollHeight;
}

$("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const field = $("message");
  const message = field.value.trim();
  if (!message) return;
  const button = $("send-button");
  showChatMessage("user", message);
  field.value = "";
  button.disabled = true;
  $("chat-status").textContent = "正在思考…";
  try {
    const data = await requestJson("/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, image_path: null, client_id: clientId, conversation_id: conversationId }), statusElement: $("chat-status"),
    });
    if (data.conversation_id) {
      conversationId = data.conversation_id;
      localStorage.setItem("adlearn_conversation_id", conversationId);
      loadHistory();
    }
    showChatMessage("agent", data.success ? (data.answer || "已完成，但没有可展示的回答。") : friendlyError(data, 200), data, !data.success);
    if (data.execution_mode === "rule_fallback") $("chat-status").textContent = "已使用规则回退完成回答";
    else $("chat-status").textContent = data.success ? "回答已完成" : "请求未完成";
    if (data.success) refreshProgress();
  } catch (error) {
    showChatMessage("agent", error.message, null, true);
    $("chat-status").textContent = "发生错误，可重新发送";
  } finally { button.disabled = false; field.focus(); }
});

$("message").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    $("chat-form").requestSubmit();
  }
});

function renderAutomation(data) {
  const panel = $("automation-result");
  panel.replaceChildren();
  panel.classList.remove("hidden");
  panel.append(node("h3", "", data.success ? "AdLearn 工作流已完成" : "AdLearn 工作流未完成"));
  const list = node("dl");
  [["Workflow", data.workflow_name], ["Trigger", data.trigger_type], ["Status", data.status],
   ["Success", String(Boolean(data.success))], ["Steps", data.steps_executed]].forEach(([key, value]) => {
    list.append(node("dt", "", key), node("dd", "", value ?? "—"));
  });
  panel.append(list);
  if (!data.success) panel.append(node("p", "notice", friendlyError(data, 200)));
  if (data.output?.summary) panel.append(node("p", "", data.output.summary));
  if (data.output?.freshness_unverified) panel.append(node("p", "notice", "当前结果未经过最新官方资料验证。"));
  if (Array.isArray(data.warnings)) data.warnings.forEach((warning) => {
    panel.append(node("p", "notice", warning.error_type === "Search API Not Configured"
      ? friendlyError(warning, 200) : (warning.message || "部分步骤未完成。")));
  });
  if (Array.isArray(data.results) && data.results.length) {
    const details = node("details");
    details.append(node("summary", "", `工具结果（${data.results.length}）`));
    data.results.forEach((item) => {
      const result = item.result || {};
      details.append(node("p", "", `${item.tool_name || "Tool"} · ${result.success ? "成功" : "失败"} · ${result.topic || result.error_type || ""}`));
    });
    panel.append(details);
  }
  if (Array.isArray(data.execution_trace)) {
    const details = node("details");
    details.append(node("summary", "", "Execution Trace"), node("pre", "", data.execution_trace.join(" → ")));
    panel.append(details);
  }
}

$("run-workflow").addEventListener("click", async () => {
  const button = $("run-workflow");
  const workflowName = $("workflow").value;
  if (workflowName !== "scheduled_ads_learning") return;
  button.disabled = true;
  $("automation-status").textContent = "工作流运行中…";
  try {
    const data = await requestJson("/automation/run", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workflow_name: workflowName, inputs: {} }), statusElement: $("automation-status"),
    });
    renderAutomation(data);
    $("automation-status").textContent = data.success ? "运行完成" : "运行未完成";
  } catch (error) {
    renderAutomation({ success: false, workflow_name: workflowName, trigger_type: "manual", status: "failed", message: error.message });
    $("automation-status").textContent = "发生错误，可重试";
  } finally { button.disabled = false; }
});

async function refreshProgress() {
  const target = $("progress-content");
  try {
    const data = await requestJson("/learning-progress");
    if (!data.success) throw new Error(friendlyError(data, 200));
    target.replaceChildren();
    [["google_ads", "Google Ads"], ["meta_ads", "Meta Ads"]].forEach(([key, title]) => {
      const item = data.progress?.[key] || {};
      const card = node("div", "progress-block");
      const top = node("div", "progress-top");
      top.append(node("strong", "", title), node("span", "progress-count", item.completed_topic_count ?? 0));
      card.append(top);
      const stats = node("div", "progress-stats");
      stats.append(node("span", "", `Concepts ${item.concept_count ?? 0}`),
                   node("span", "", `Steps ${item.step_count ?? 0}`),
                   node("span", "", `Analysis ${item.analysis_count ?? 0}`));
      card.append(stats);
      target.append(card);
    });
    target.append(node("p", "recent", `Recent Learning：${data.recent_topic || "暂无记录"}`));
  } catch (error) { target.replaceChildren(node("p", "notice", error.message)); }
}

async function refreshStatus() {
  const target = $("system-status");
  try {
    const data = await requestJson("/api/status");
    target.replaceChildren();
    [[`Service · ${data.service_name || "AdLearn"}`, data.service === "online"], ["LLM", data.llm_enabled],
     ["Vision", data.vision_enabled], ["Search", data.search_configured], ["Database", data.database_connected]].forEach(([label, active]) => {
      const row = node("div", "status-row");
      const value = label === "Database" ? (active ? "Connected" : data.database_configured ? "Disconnected" : "Not Configured") :
                    label === "Search" ? (active ? "Configured" : "Not Configured") :
                    label.startsWith("Service") ? (active ? "Online" : "Offline") : (active ? "Enabled" : "Disabled");
      row.append(node("span", "", label), node("strong", active ? "state-on" : "state-off", value));
      target.append(row);
    });
    $("service-indicator").classList.toggle("online", data.service === "online");
  } catch (error) {
    target.replaceChildren(node("p", "notice", error.message));
    $("service-indicator").classList.remove("online");
  }
}

$("refresh-progress").addEventListener("click", refreshProgress);
refreshStatus();
refreshProgress();
loadHistory().then(() => { if (conversationId) openConversation(conversationId); });
