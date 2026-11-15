from typing import Union

from iso639 import Language
from py3langid.langid import MODEL_FILE, LanguageIdentifier
from resiliparse.parse.html import HTMLTree
from resiliparse.parse.lang import detect_fast

IDENTIFIER = LanguageIdentifier.from_pickled_model(MODEL_FILE)
MAX_LEN = 1_000


def identify_language(
    tree: HTMLTree, description: str, plain_text: str
) -> Union[str, None]:
    """
    Identifies the language of an HTML based on the corresponding HTMLTree.
    This is done in hierarchical steps to be as efficient as possible:
    1. Lang attribute of the HTML
    2. Classification of the plain text with resiliparse
    3. Classification of the description with py3langid
    4. Classification of the plain text with py3langid

    :param tree:        The HTMLTree instance from which to extract title and description
    :param description: The description from the document metadata
    :param plain_text:  The plain text as extracted by resiliparse.extract.html2text
    :return:            Standardized language code (ISO 639-3:2007) or None
    """
    language = None
    rp_cutoff = 500  # Increase this value to be more efficient at the expense of classification quality
    pl_cutoff = -100

    # Reduce the size of the plain text to avoid overflow errors in py3langid
    plain_text = plain_text[:MAX_LEN].strip()

    # 1. Check if the html node has a valid lang attribute
    node = tree.document.query_selector("html[lang]")
    if node is not None:
        language = node.getattr("lang").lower()
        if "-" in language:
            language = language.split("-")[0]
        # Handle faulty input
        try:
            _ = Language.match(language)
        except:
            language = None

    # 2. Resiliparse on plain text
    if language is None and plain_text is not None:
        language = _rp_classification(text=plain_text, rp_cutoff=rp_cutoff)

    # 3. py3langid on description
    if language is None and description is not None:
        language = _pl_classification(text=description, pl_cutoff=pl_cutoff)

    # 4. py3langid on plain text
    if language is None and plain_text is not None:
        language = _pl_classification(text=plain_text, pl_cutoff=pl_cutoff)

    # Return the predicted language in ISO 639:3 or None
    if language is None:
        return None
    else:
        return Language.match(language).part3


def _rp_classification(text: str, rp_cutoff: int):
    """
    Use Resiliparse for language classification.
    The second value is the out-of-place-measure, higher mean less confident.
    """
    rp_prediction = detect_fast(text)
    if rp_prediction[0] != "unknown" and rp_prediction[1] < rp_cutoff:
        return rp_prediction[0]
    return None


def _pl_classification(text: str, pl_cutoff: int):
    """
    Use py3langid for language classification.
    The second value is the unnormalized probabability, higher means less confident.
    """
    pl_prediction = IDENTIFIER.classify(text)
    if pl_prediction[1] < pl_cutoff:
        return pl_prediction[0]
    return None
