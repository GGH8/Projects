-- 1. Use the terminal's 16 ANSI colors instead of a custom Neovim theme
vim.cmd('colorscheme default')
-- vim.opt.termguicolors = false -- Uncomment if you need to force exactly 16 colors

-- 2. Make the background completely transparent to match Kitty's background
vim.api.nvim_set_hl(0, "Normal", { bg = "none" })
vim.api.nvim_set_hl(0, "NormalFloat", { bg = "none" })
vim.api.nvim_set_hl(0, "LineNr", { bg = "none" })

-- Set absolute line numbers
vim.opt.number = true
-- (Optional) Add relative line numbers if you like that style:
-- vim.opt.relativenumber = true

-- Set leader key to Space
vim.g.mapleader = " "

-- General Keymaps
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>', { desc = 'Clear search highlights' })
vim.keymap.set('n', '<C-h>', '<C-w><C-h>', { desc = 'Move focus to the left window' })
vim.keymap.set('n', '<C-l>', '<C-w><C-l>', { desc = 'Move focus to the right window' })
vim.keymap.set('n', '<C-j>', '<C-w><C-j>', { desc = 'Move focus to the lower window' })
vim.keymap.set('n', '<C-k>', '<C-w><C-k>', { desc = 'Move focus to the upper window' })

-- Git Keymaps (Fugitive)
vim.keymap.set('n', '<leader>gs', vim.cmd.Git, { desc = 'Open full Git status menu' })
vim.keymap.set('n', '<leader>gb', function() vim.cmd('Git blame') end, { desc = 'Open full Git blame' })


-- Diagnostic keymaps
vim.keymap.set('n', 'gl', vim.diagnostic.open_float, { desc = 'Show diagnostic error messages' })
vim.keymap.set('n', '[d', vim.diagnostic.goto_prev, { desc = 'Go to previous diagnostic message' })
vim.keymap.set('n', ']d', vim.diagnostic.goto_next, { desc = 'Go to next diagnostic message' })
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostic list' })

-- 1. Bootstrapping Lazy.nvim (Plugin Manager)
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- 2. Setup Plugins
require("lazy").setup({
  -- Git & GitHub Integration
  "tpope/vim-fugitive",        -- The best Git wrapper for Vim
  {
    "lewis6991/gitsigns.nvim", -- Shows git add/delete/change signs in the left column
    opts = {
      signs = {
        add          = { text = '┃' },
        change       = { text = '┃' },
        delete       = { text = '_' },
        topdelete    = { text = '‾' },
        changedelete = { text = '~' },
      },
      on_attach = function(bufnr)
        local gs = package.loaded.gitsigns

        local function map(mode, l, r, opts)
          opts = opts or {}
          opts.buffer = bufnr
          vim.keymap.set(mode, l, r, opts)
        end

        -- Navigation
        map('n', ']c', function()
          if vim.wo.diff then return ']c' end
          vim.schedule(function() gs.next_hunk() end)
          return '<Ignore>'
        end, {expr=true, desc = 'Next git hunk'})

        map('n', '[c', function()
          if vim.wo.diff then return '[c' end
          vim.schedule(function() gs.prev_hunk() end)
          return '<Ignore>'
        end, {expr=true, desc = 'Previous git hunk'})

        -- Actions
        map('n', '<leader>hs', gs.stage_hunk, { desc = 'Stage git hunk' })
        map('n', '<leader>hr', gs.reset_hunk, { desc = 'Reset git hunk' })
        map('n', '<leader>hp', gs.preview_hunk, { desc = 'Preview git hunk' })
        map('n', '<leader>hb', function() gs.blame_line{full=true} end, { desc = 'Git blame line' })
      end
    }
  },

  -- LSP Support
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      -- Automatically install LSPs to stdpath for neovim
      { "williamboman/mason.nvim", config = true },
      "williamboman/mason-lspconfig.nvim",
      -- Useful status updates for LSP
      { "j-hui/fidget.nvim", opts = {} },
    },
  },

  -- Autocompletion
  {
    "hrsh7th/nvim-cmp",
    dependencies = {
      -- Snippet Engine & its associated nvim-cmp source
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
      -- Adds LSP completion capabilities
      "hrsh7th/cmp-nvim-lsp",
      -- Adds a number of user-friendly snippets
      "rafamadriz/friendly-snippets",
    },
  },
})

-- 3. Configure Mason (LSP Installer)
require("mason").setup()
require("mason-lspconfig").setup({
  ensure_installed = { "pyright" }, -- Autoinstalls the Python LSP
})

-- 4. Autocompletion configuration (nvim-cmp)
local cmp = require('cmp')
local luasnip = require('luasnip')
require('luasnip.loaders.from_vscode').lazy_load()

cmp.setup({
  snippet = {
    expand = function(args)
      luasnip.lsp_expand(args.body)
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ['<C-b>'] = cmp.mapping.scroll_docs(-4),
    ['<C-f>'] = cmp.mapping.scroll_docs(4),
    ['<C-Space>'] = cmp.mapping.complete(),
    ['<CR>'] = cmp.mapping.confirm({ select = true }), -- Accept currently selected item.
    ['<Tab>'] = cmp.mapping(function(fallback)
      if cmp.visible() then
        cmp.select_next_item()
      elseif luasnip.expand_or_jumpable() then
        luasnip.expand_or_jump()
      else
        fallback()
      end
    end, { 'i', 's' }),
    ['<S-Tab>'] = cmp.mapping(function(fallback)
      if cmp.visible() then
        cmp.select_prev_item()
      elseif luasnip.jumpable(-1) then
        luasnip.jump(-1)
      else
        fallback()
      end
    end, { 'i', 's' }),
  }),
  sources = {
    { name = 'nvim_lsp' },
    { name = 'luasnip' },
  },
})

-- 5. Enable the Python LSP (Pyright) using Neovim 0.11 native config
local capabilities = require("cmp_nvim_lsp").default_capabilities()

vim.lsp.config('pyright', {
  capabilities = capabilities,
})
vim.lsp.enable('pyright')

-- LSP Keymaps
vim.keymap.set('n', 'gd', vim.lsp.buf.definition, { desc = 'Go to definition' })
vim.keymap.set('n', 'gr', vim.lsp.buf.references, { desc = 'Go to references' })
vim.keymap.set('n', 'gD', vim.lsp.buf.declaration, { desc = 'Go to declaration' })
vim.keymap.set('n', 'K', vim.lsp.buf.hover, { desc = 'Hover Documentation' })
vim.keymap.set('n', '<leader>r', vim.lsp.buf.rename, { desc = 'Rename variable' })
vim.keymap.set('n', '<leader>ca', vim.lsp.buf.code_action, { desc = 'Code action' })
