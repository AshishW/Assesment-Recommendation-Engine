import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)  # all-MiniLM-L6-v2
vector_db = FAISS.load_local(
    "shl_faiss_index", embeddings, allow_dangerous_deserialization=True
)


def get_ground_truth():
    df = pd.read_csv("train_set.csv")

    query_col = df.columns[0]
    url_col = df.columns[1]

    ground_truth = {}
    for _, row in df.iterrows():
        query = str(row[query_col])
        url = str(row[url_col])
        if query not in ground_truth:
            ground_truth[query] = set()
        ground_truth[query].add(url)
    return ground_truth


# ground_truth = get_ground_truth()

# query = "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."  # Replace with a REAL query from your CSV that failed
# query = "I want to hire new graduates for a sales role in my company, the budget is for about an hour for each test. Give me some options"
query = """
Find me 1 hour long assesment for the below job at SHL
Job Description

 Join a community that is shaping the future of work! SHL, People Science. People Answers.

Are you a seasoned QA Engineer with a flair for innovation? Are you ready to shape the future of talent assessment and empower organizations to unlock their full potential? If so, we want you to be a part of the SHL Team! As a QA Engineer, you will be involved in creating and implementing software solutions that contribute to the development of our ground-breaking products.

An excellent benefit package is offered in a culture where career development, with ongoing manager guidance, collaboration, flexibility, diversity, and inclusivity are all intrinsic to our culture.  There is a huge investment in SHL currently so there’s no better time to become a part of something transformational.

What You Will Be Doing

 Getting involved in engineering quality assurance and providing inputs when required.
 Create and develop test plans for various forms of testing.
 Conducts and/or participates in formal and informal test case reviews.
 Develop and initiate functional tests and regression tests.
 Rolling out improvements for testing and quality processes.

Essential

 What we are looking for from you:

 Development experience – Java or JavaScript, CSS, HTML (Automation)
 Selenium WebDriver and page object design pattern (Automation)
 SQL server knowledge
 Test case management experience.
 Manual Testing

Desirable

 Knowledge the basic concepts of testing
 Strong solution-finding experience
 Strong verbal and written communicator.

Get In Touch

Find out how this one-off opportunity can help you achieve your career goals by making an application to our knowledgeable and friendly Talent Acquisition team. Choose a new path with SHL.

 #CareersAtSHL #SHLHiringTalent

#TechnologyJobs #QualityAssuranceJobs

#CareerOpportunities #JobOpportunities

About Us

We unlock the possibilities of businesses through the power of people, science and technology.
We started this industry of people insight more than 40 years ago and continue to lead the market with powerhouse product launches, ground-breaking science and business transformation.
When you inspire and transform people’s lives, you will experience the greatest business outcomes possible. SHL’s products insights, experiences, and services can help achieve growth at scale.

What SHL Can Offer You

Diversity, equity, inclusion and accessibility are key threads in the fabric of SHL’s business and culture (find out more about DEI and accessibility at SHL )
Employee benefits package that takes care of you and your family.
Support, coaching, and on-the-job development to achieve career success
A fun and flexible workplace where you’ll be inspired to do your best work (find out more LifeAtSHL )
The ability to transform workplaces around the world for others.

SHL is an equal opportunity employer. We support and encourage applications from a diverse range of candidates. We can, and do make adjustments to make sure our recruitment process is as inclusive as possible.

SHL is an equal opportunity employer.
"""
# correct_url_part = "automata-fix-new"
# correct_url_part = "entry-level-sales-7-1"
correct_url_part = "manual-testing-new"


docs = vector_db.similarity_search(query, k=20)

print(f"Query: {query}")
print(f"Looking for: {correct_url_part}")
print("-" * 30)

found_at = -1
for i, d in enumerate(docs):
    print(f"Rank {i + 1}: {d.metadata['name']} | {d.metadata['url']}")
    if correct_url_part in d.metadata["url"]:
        found_at = i + 1

print("-" * 30)
if found_at != -1:
    print(f"SUCCESS: Found at Rank {found_at}")
else:
    print("FAILURE: Not in Top 20")
