"""start the local LLM"""

import qdrant_client
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
from langchain.embeddings import LlamaCppEmbeddings
from langchain.vectorstores import Qdrant

from load_env import llama_embeddings_model, model_n_ctx, model_path, model_stop, model_temp, model_type, persist_directory, use_mlock

qa_system = None


def initialize_qa_system():
    global qa_system
    if qa_system is None:
        # Load stored vectorstore
        llama = LlamaCppEmbeddings(model_path=llama_embeddings_model, n_ctx=model_n_ctx)
        # Load ggml-formatted model
        local_path = model_path

        client = qdrant_client.QdrantClient(path=persist_directory, prefer_grpc=True)
        qdrant = Qdrant(client=client, collection_name="test", embeddings=llama)

        # Prepare the LLM chain
        callbacks = [StreamingStdOutCallbackHandler()]
        match model_type:
            case "LlamaCpp":
                from langchain.llms import LlamaCpp

                llm = LlamaCpp(
                    model_path=local_path,
                    n_ctx=model_n_ctx,
                    temperature=model_temp,
                    stop=model_stop,
                    callbacks=callbacks,
                    verbose=True,
                    n_threads=6,
                    n_batch=1000,
                    use_mlock=use_mlock,
                )
            case "GPT4All":
                from langchain.llms import GPT4All

                llm = GPT4All(
                    model=local_path,
                    n_ctx=model_n_ctx,
                    callbacks=callbacks,
                    verbose=True,
                    backend="gptj",
                )
            case _default:
                print("Only LlamaCpp or GPT4All supported right now. Make sure you set up your .env correctly.")
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=qdrant.as_retriever(search_type="mmr"),
            return_source_documents=True,
        )
        qa_system = qa


def main():
    initialize_qa_system()
    # Interactive questions and answers
    while True:
        query = input("\nEnter a query: ")
        if query == "exit":
            break
        elif not query.strip():  # check if query empty
            print("Empty query, skipping")
            continue

        # Get the answer from the chain
        res = qa_system(query)
        answer, docs = res["result"], res["source_documents"]

        # Print the result
        print("\n\n> Question:")
        print(query)
        print("\n> Answer:")
        print(answer)

        # Print the relevant sources used for the answer
        for document in docs:
            print("\n> " + document.metadata["source"] + ":")
            print(document.page_content)


if __name__ == "__main__":
    main()
