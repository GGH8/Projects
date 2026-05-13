import os

config_path = os.path.expanduser("~/.config/nvim/init.lua")

with open(config_path, "r") as f:
    content = f.read()

deprecated_snippet = """require('lspconfig').pyright.setup {
  capabilities = capabilities,
}"""

new_snippet = """vim.lsp.config('pyright', {
  capabilities = capabilities,
})
vim.lsp.enable('pyright')"""

if deprecated_snippet in content:
    content = content.replace(deprecated_snippet, new_snippet)
    with open(config_path, "w") as f:
        f.write(content)
    print("Successfully updated init.lua to remove deprecated lspconfig setup.")
else:
    print("Deprecated snippet not found. File may already be updated or structured differently.")
