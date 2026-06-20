import { BROWSER_EXTENSION_ATTRIBUTES } from "@/lib/browser-extension-attributes";
import { sidebarInitScript } from "@/lib/sidebar-script";
import { themeInitScript } from "@/lib/theme-script";

/**
 * Runs theme/sidebar init and strips extension-injected DOM before React hydrates.
 * Single inline script in <body> avoids head script tags that extensions often rewrite.
 */
export function PreHydrationScripts() {
  const attrsJson = JSON.stringify(BROWSER_EXTENSION_ATTRIBUTES);

  const script = `
(function () {
  var ATTRS = ${attrsJson};

  function isExtensionScript(node) {
    if (!node || node.nodeType !== 1 || node.tagName !== "SCRIPT") return false;
    var src = node.getAttribute("src") || "";
    return (
      src.indexOf("chrome-extension://") === 0 ||
      src.indexOf("moz-extension://") === 0 ||
      node.hasAttribute("bis_use")
    );
  }

  function strip(node) {
    if (!node || node.nodeType !== 1) return;
    if (isExtensionScript(node)) {
      node.parentNode && node.parentNode.removeChild(node);
      return;
    }
    for (var i = 0; i < ATTRS.length; i++) {
      var name = ATTRS[i];
      if (node.hasAttribute(name)) node.removeAttribute(name);
    }
    var children = node.children;
    for (var j = 0; j < children.length; j++) strip(children[j]);
  }

  function cleanupExtensions() {
    if (typeof document === "undefined") return;
    strip(document.documentElement);
    var scripts = document.getElementsByTagName("script");
    for (var k = scripts.length - 1; k >= 0; k--) {
      if (isExtensionScript(scripts[k])) {
        scripts[k].parentNode && scripts[k].parentNode.removeChild(scripts[k]);
      }
    }
  }

  cleanupExtensions();

  ${themeInitScript}
  ${sidebarInitScript}

  if (typeof MutationObserver !== "undefined") {
    new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var mutation = mutations[i];
        if (mutation.type === "childList") {
          mutation.addedNodes.forEach(function (node) {
            strip(node);
          });
        } else if (
          mutation.type === "attributes" &&
          mutation.attributeName &&
          ATTRS.indexOf(mutation.attributeName) !== -1
        ) {
          mutation.target.removeAttribute(mutation.attributeName);
        }
      }
    }).observe(document.documentElement, {
      attributes: true,
      childList: true,
      subtree: true,
      attributeFilter: ATTRS,
    });
  }
})();
`.trim();

  return (
    <script
      id="pre-hydration-init"
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: script }}
    />
  );
}
