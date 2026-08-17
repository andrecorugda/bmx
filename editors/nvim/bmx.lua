-- Neovim: source this, or copy it into your config.
--
-- Filetype detection plus the two settings a markup file wants. Highlighting
-- comes from the TextMate grammar via any plugin that reads one; there is no
-- tree-sitter parser for BMX and this file does not pretend there is.
vim.filetype.add({ extension = { bmx = "bmx" } })

-- Diagnostics, via the language server. Needs node and nothing else.
--
-- Point `cmd` at your checkout. Using vim.lsp.start rather than nvim-lspconfig so this file has no
-- plugin dependency — a config that needs a plugin manager is a config half of readers cannot use.
local bmx_lsp = vim.fn.expand("~/bmx/editors/lsp/bmx-lsp.mjs")

vim.api.nvim_create_autocmd("FileType", {
  pattern = "bmx",
  callback = function(event)
    if vim.fn.filereadable(bmx_lsp) == 1 then
      vim.lsp.start({
        name = "bmx-lsp",
        cmd = { "node", bmx_lsp },
        root_dir = vim.fs.dirname(vim.api.nvim_buf_get_name(event.buf)),
      })
    end
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = "bmx",
  callback = function()
    vim.opt_local.expandtab = true
    vim.opt_local.shiftwidth = 2
    vim.opt_local.commentstring = "<!-- %s -->"
    -- A block fence and a slot are the two things worth jumping between.
    vim.opt_local.matchpairs:append("{:}")
  end,
})
