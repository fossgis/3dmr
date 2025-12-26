# Bootstrap Migration Tracker

## Files to Migrate (from audit)
- [ ] layout.html - navbar-inverse → navbar-dark bg-dark
- [ ] docs.html - MANY panels (10+ API endpoint panels)
- [ ] modelpanel.html - panel structure, labels, col-xs-12
- [ ] model.html - panels, tab-pane
- [ ] modelform.html - form-group (8 instances)
- [ ] model_overview.html - labels, btn-default
- [ ] index.html - btn-default
- [ ] search.html - btn-default
- [ ] user.html - btn-default
- [ ] user_form.html - form-group

## Bootstrap 3 Classes Found (from audit)
- `.panel` → `.card` (40+ instances!)
- `.panel-heading` → `.card-header`
- `.panel-body` → `.card-body`
- `.panel-title` → `.card-title`
- `.label label-default` → `.badge bg-secondary` (15+ instances)
- `.label label-success` → `.badge bg-success`
- `.label label-danger` → `.badge bg-danger`
- `.btn-default` → `.btn-secondary` (10+ instances)
- `.form-group` → `.mb-3` (10+ instances)
- `.col-xs-12` → `.col-12`
- `.navbar-inverse` → `.navbar-dark bg-dark`
- `.tab-pane` → stays same (works in BS5)

## Status
- [x] Audit completed
- [ ] Bootstrap assets replaced
- [ ] Layout.html migrated
- [ ] All templates migrated
- [ ] Testing completed