// Accessibility of the two form inputs.
//
// Both labels were siblings of their input with no htmlFor and the inputs had
// no id, so neither was programmatically labelled and a screen reader announced
// them as unlabelled fields. These locate the inputs the way a user of
// assistive technology would: by their accessible name, not by placeholder or
// by CSS selector.

// Cypress specs execute in a separate frame from the app under test, so the
// bare `document` global is the spec document, not the one holding the input.
// Every lookup therefore goes through the element's own ownerDocument.
const accessibleName = (el) => {
  const doc = el.ownerDocument
  const explicit = doc.querySelector('label[for="' + el.id + '"]')
  if (explicit) return explicit.textContent.trim()
  if (el.getAttribute('aria-label')) return el.getAttribute('aria-label')
  const labelledBy = el.getAttribute('aria-labelledby')
  const node = labelledBy ? doc.getElementById(labelledBy) : null
  if (node) return node.textContent.trim()
  const wrapping = el.closest('label')
  if (wrapping) return wrapping.textContent.trim()
  return ''
}

describe('form inputs have accessible names', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('exposes the SMILES field by its visible label text', () => {
    cy.contains('label', 'Base Molecule SMILES').should('exist')
    cy.get('input#base-molecule-smiles')
      .should('exist')
      .then(($el) => {
        expect(accessibleName($el[0]), 'SMILES input has no accessible name').to.equal(
          'Base Molecule SMILES'
        )
      })
  })

  it('exposes the mutations field by its visible label text', () => {
    cy.contains('label', 'Number of Mutations').should('exist')
    cy.get('input#number-of-mutations')
      .should('exist')
      .then(($el) => {
        expect(
          accessibleName($el[0]),
          'mutations input has no accessible name'
        ).to.equal('Number of Mutations')
      })
  })

  it('ties each label to its input with label[for] matching the input id', () => {
    // The specific mechanism that was missing. Asserting on the pair directly
    // rather than on computed names keeps the intent visible.
    cy.get('label[for="base-molecule-smiles"]').should('contain.text', 'SMILES')
    cy.get('label[for="number-of-mutations"]').should('contain.text', 'Mutations')
  })

  it('keeps ids unique across the document', () => {
    cy.get('[id]').then(($els) => {
      const ids = $els.toArray().map((e) => e.id)
      const dupes = ids.filter((id, i) => ids.indexOf(id) !== i)
      expect(dupes, `duplicate ids: ${dupes.join(', ')}`).to.have.length(0)
    })
  })
})

describe('mutation bounds reflect the API contract', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('permits zero, which the API accepts and answers with mutated=false', () => {
    // min was 1, contradicting the server, whose lower bound is non-negative.
    cy.get('input#number-of-mutations').should('have.attr', 'min', '0')
  })

  it('keeps the upper bound at the server limit', () => {
    cy.get('input#number-of-mutations').should('have.attr', 'max', '10')
  })

  it('defaults to 3, matching the API default', () => {
    cy.get('input#number-of-mutations').should('have.value', '3')
  })
})
