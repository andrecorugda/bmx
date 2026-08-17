-- Neovim: source this, or copy it into your config.
--
-- Filetype detection plus the two settings a markup file wants. Highlighting
-- comes from the TextMate grammar via any plugin that reads one; there is no
-- tree-sitter parser for BMX and this file does not pretend there is.
vim.filetype.add({ extension = { bmx = "bmx" } })

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
