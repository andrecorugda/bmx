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
-- Built once: `burxt build editors/lsp/bmx-lsp.bx -o ~/bin/bmx-lsp`. It needs no runtime;
-- it was a node script until the server was ported to Burxt.
local bmx_lsp = vim.fn.expand("~/bin/bmx-lsp")

vim.api.nvim_create_autocmd("FileType", {
  pattern = "bmx",
  callback = function(event)
    if vim.fn.filereadable(bmx_lsp) == 1 then
      vim.lsp.start({
        name = "bmx-lsp",
        cmd = { bmx_lsp },
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
    -- A slot, so `%` jumps between `{{` and `}}`. **Not the fence**, and the comment here used to
    -- imply otherwise: `matchpairs` takes two DIFFERENT characters, and a block's `:name:` /
    -- `:!name:` are neither single nor different. Jumping between those wants `matchit`'s
    -- `b:match_words`, which is a feature this file does not have rather than one it provides.
    vim.opt_local.matchpairs:append("{:}")
  end,
})
