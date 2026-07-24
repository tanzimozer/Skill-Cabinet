# Profile JSON Field Mapping

The spec docs reference fields differently than the actual JSON structure. Use this mapping:

## Contact
- Spec: `contact.name`, `contact.phone`, `contact.email`, `contact.city`
- Actual: Same, plus `contact.linkedin`, `contact.github`, `contact.credential`, `contact.remote_flag`

## Roles
- Spec: `role.title`
- Actual: `role.default_title` (or `role.title_options[]` for variants)

## Skills
- Spec: `skills.core[]`, `skills.swappable[]`
- Actual: `core_skills[]`, `swappable_skills[]` (top-level arrays)

## Bullets
- Spec: `role.bullets[]` as strings
- Actual: `role.bullets[]` as objects with `{text, tags[], closer?}`

## Certifications
- Spec: `certifications[].name`
- Actual: `certifications[]` as plain strings

## Projects  
- Spec: `projects[].name`
- Actual: `projects[]` as plain strings

## Summary
- Spec: `professional_summary.default`
- Actual: May not exist; build from `achievements_pool[]` instead
