"use strict";

const $ = (id) => document.getElementById(id);
const conversation = $("conversation");
const clientId = localStorage.getItem("adlearn_client_id") || crypto.randomUUID();
localStorage.setItem("adlearn_client_id", clientId);
let conversationId = localStorage.getItem("adlearn_conversation_id");

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
      const remove = node("button", "history-delete", "Delete");
      remove.type = "button";
      remove.setAttribute("aria-label", `删除 ${item.title}`);
      remove.addEventListener("click", async () => {
        if (!confirm("确定删除这个对话吗？")) return;
        try {
          await requestJson(`/conversations/${item.id}?client_id=${encodeURIComponent(clientId)}`, { method: "DELETE" });
          if (conversationId === item.id) newChat();
          await loadHistory();
        } catch (error) { $("history-status").textContent = error.message; }
      });
      row.append(open, remove);
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
    data.messages.forEach((item) => showChatMessage(item.role === "user" ? "user" : "agent", item.content));
    await loadHistory();
  } catch (error) { $("history-status").textContent = error.message; }
}

function newChat() {
  conversationId = null;
  localStorage.removeItem("adlearn_conversation_id");
  clearConversation();
  $("message").focus();
}

$("new-chat").addEventListener("click", () => { newChat(); loadHistory(); });

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
    if (status) status.textContent = "服务正在启动，请稍候……";
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
    if (error.name === "AbortError") throw new Error("请求超时。服务可能正在启动，请稍后重试。");
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

function showChatMessage(role, text, data = null, isError = false) {
  const empty = conversation.querySelector(".empty-chat");
  if (empty) empty.remove();
  const wrapper = node("div", `message ${role}`);
  wrapper.append(node("span", "message-label", role === "user" ? "You" : "Agent"));
  wrapper.append(node("div", `bubble${isError ? " error" : ""}`, text));
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
