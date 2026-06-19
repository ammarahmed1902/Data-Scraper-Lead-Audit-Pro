import { BROWSER_EXTENSION_ATTRIBUTES } from "@/lib/browser-extension-attributes";

/**
 * Strips extension-injected attributes before React hydrates.
 * Must be an inline script (not useEffect) because effects run after hydration.
 */
export function BrowserExtensionHydrationScript() {
  const attrsJson = JSON.stringify(BROWSER_EXTENSION_ATTRIBUTES);

  return (
    <script
      id="browser-extension-hydration-fix"
      dangerouslySetInnerHTML={{
        __html: `
(function () {
  var ATTRS = ${attrsJson};

  function strip(node) {
    if (!node || node.nodeType !== 1) return;
    for (var i = 0; i < ATTRS.length; i++) {
      var name = ATTRS[i];
      if (node.hasAttribute(name)) node.removeAttribute(name);
    }
    var children = node.children;
    for (var j = 0; j < children.length; j++) strip(children[j]);
  }

  function run() {
    if (typeof document === "undefined") return;
    strip(document.documentElement);
  }

  run();

  if (typeof MutationObserver !== "undefined" && typeof document !== "undefined") {
    new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var mutation = mutations[i];
        if (
          mutation.type === "attributes" &&
          mutation.attributeName &&
          ATTRS.indexOf(mutation.attributeName) !== -1
        ) {
          mutation.target.removeAttribute(mutation.attributeName);
        } else if (mutation.type === "childList") {
          mutation.addedNodes.forEach(function (node) {
            strip(node);
          });
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
        `.trim(),
      }}
    />
  );
}
